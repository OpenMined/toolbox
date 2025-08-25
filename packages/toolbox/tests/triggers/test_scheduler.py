import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from pytest import MonkeyPatch
from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB, utcnow


@pytest.fixture
def event_script_path(test_assets_dir: Path) -> Path:
    """Path to the test script for integration tests"""
    script_path = test_assets_dir / "event_script.py"
    assert script_path.exists(), f"Test script not found: {script_path}"
    return script_path


@pytest.fixture
def db() -> TriggerDB:
    """Create an in-memory test database"""
    return TriggerDB.from_url("sqlite:///:memory:")


@pytest.fixture
def scheduler(db: TriggerDB) -> Scheduler:
    """Create a scheduler with test database"""
    yield Scheduler(db)


@pytest.fixture
def script_summary_file(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Manages test output file cleanup with unique paths per test"""
    summary_file = tmp_path / "test_script_output.json"
    # Set environment variable so the test script knows where to write
    monkeypatch.setenv("TEST_SCRIPT_OUTPUT_FILE", str(summary_file))
    yield summary_file
    # tmp_path and monkeypatch automatically clean up after test


def read_script_output(summary_file: Path) -> Dict[str, Any]:
    """Helper to read and parse script output"""
    assert summary_file.exists(), "Script should have created summary file"
    with open(summary_file, "r") as f:
        return json.load(f)


def create_test_events(db: TriggerDB, now: datetime) -> Dict[str, Any]:
    """Helper to create common test events"""
    return {
        "slack_message": db.events.create(
            name="message_created",
            source="slack",
            data={"text": "slack"},
            timestamp=now,
        ),
        "discord_message": db.events.create(
            name="message_created",
            source="discord",
            data={"text": "discord"},
            timestamp=now,
        ),
        "slack_dm": db.events.create(
            name="dm_sent", source="slack", data={"text": "private"}, timestamp=now
        ),
        "obsidian_note": db.events.create(
            name="note_created",
            source="obsidian",
            data={"title": "test"},
            timestamp=now,
        ),
    }


def test_scheduler_finds_due_triggers(scheduler: Scheduler, tmp_path: Path) -> None:
    """Test scheduler gets due triggers from database efficiently"""
    now = utcnow()

    # Create a due trigger (past next_run_at)
    due_trigger = scheduler.db.triggers.create(
        name="due-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )
    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        due_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Create a future trigger (not due)
    scheduler.db.triggers.create(
        name="future-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )

    # Test that _process_triggers submits due triggers to executor
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor)

    # Should submit only the due trigger to executor
    mock_executor.submit.assert_called_once()
    call_args = mock_executor.submit.call_args[0]
    assert call_args[0] == scheduler.execute_trigger  # method
    assert call_args[1].id == due_trigger.id  # trigger


def test_scheduler_updates_next_run_before_execution(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test _process_triggers updates next_run_at before execution"""
    import time

    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )
    # Make trigger due
    past_time = utcnow() - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Small delay to ensure different next_run_at calculation
    time.sleep(0.1)

    original_next_run = scheduler.db.triggers.get(trigger.id).next_run_at

    mock_executor = Mock()
    scheduler._process_triggers(mock_executor)

    # Verify next_run_at was updated before execution
    updated_trigger = scheduler.db.triggers.get(trigger.id)
    assert updated_trigger.next_run_at != original_next_run

    # Verify executor.submit was called
    mock_executor.submit.assert_called_once()


def test_scheduler_handles_event_based_triggers(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test scheduler processes event-based triggers correctly"""
    now = utcnow()

    event_trigger = scheduler.db.triggers.create(
        name="event-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
        event_names=["test_event"],
    )

    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        event_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    _ = scheduler.db.events.create(
        name="test_event",
        source="test_source",
        data={"key": "value"},
        timestamp=utcnow(),
    )

    # Test _process_triggers submits event-based trigger to executor
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor)

    # Should submit trigger to executor (events are fetched inside execute_trigger)
    mock_executor.submit.assert_called_once()
    call_args = mock_executor.submit.call_args[0]
    assert call_args[0] == scheduler.execute_trigger  # method
    assert call_args[1].id == event_trigger.id  # trigger


def test_scheduler_skips_triggers_with_no_events(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test scheduler skips event triggers when no events available"""
    now = utcnow()

    # Create event-based trigger with no matching events
    event_trigger = scheduler.db.triggers.create(
        name="event-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
        event_names=["nonexistent_event"],
    )
    # Set as due
    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        event_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Test _process_triggers still submits the trigger (events check happens in execute_trigger)
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor)

    # Should submit trigger to executor (it will check for events internally)
    mock_executor.submit.assert_called_once()
    call_args = mock_executor.submit.call_args[0]
    assert call_args[0] == scheduler.execute_trigger
    assert call_args[1].id == event_trigger.id


def test_execute_trigger_creates_execution_record(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test execute_trigger creates database execution record"""
    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        scheduler.execute_trigger(trigger)

        # Verify execution record was created
        executions = scheduler.db.executions.get_all(trigger_id=trigger.id)
        assert len(executions) == 1
        assert executions[0].trigger_id == trigger.id


def test_execute_from_scheduler_updates_next_run_time(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test scheduler._process_triggers method updates next_run_at before executing"""
    import time

    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )
    # Make trigger due
    past_time = utcnow() - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    original_next_run = scheduler.db.triggers.get(trigger.id).next_run_at

    # Small delay to ensure different next_run_at calculation
    time.sleep(0.1)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        mock_executor = Mock()
        scheduler._process_triggers(mock_executor)

        # Verify next_run_at was updated
        updated_trigger = scheduler.db.triggers.get(trigger.id)
        assert updated_trigger.next_run_at != original_next_run


def test_execute_trigger_does_not_update_next_run_time(
    scheduler: Scheduler, tmp_path: Path
) -> None:
    """Test execute_trigger (CLI method) doesn't affect scheduling"""
    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(tmp_path / "test.py"),
    )
    original_next_run = trigger.next_run_at

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        scheduler.execute_trigger(trigger)

        # Verify next_run_at was NOT updated
        updated_trigger = scheduler.db.triggers.get(trigger.id)
        assert updated_trigger.next_run_at == original_next_run


def test_execute_trigger_with_script(
    scheduler: Scheduler, event_script_path: Path, script_summary_file: Path
) -> None:
    """Integration test: Basic script execution and event passing"""

    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(event_script_path),
        event_names=["test_event"],
    )

    now = utcnow()
    slack_event = scheduler.db.events.create(  # noqa: F841
        name="test_event",
        source="slack",
        data={"message": "hello world"},
        timestamp=now,
    )
    discord_event = scheduler.db.events.create(  # noqa: F841
        name="test_event",
        source="discord",
        data={"message": "hello discord"},
        timestamp=now,
    )

    # Execute trigger
    matching_events = scheduler.db.events.get_events_for_trigger(
        trigger, is_consumed=False
    )
    scheduler.execute_trigger(trigger, matching_events)

    # Verify execution record
    executions = scheduler.db.executions.get_all(trigger_id=trigger.id)
    assert len(executions) == 1
    assert executions[0].completed_at is not None
    assert executions[0].exit_code == 0

    # Verify script received events
    summary = read_script_output(script_summary_file)
    assert summary["events_received"] == 2
    assert "test_event" in summary["event_names"]
    assert "slack" in summary["event_sources"]
    assert "discord" in summary["event_sources"]


def test_execute_trigger_event_name_filtering(
    scheduler: Scheduler, event_script_path: Path, script_summary_file: Path
) -> None:
    """Integration test: Event filtering by name"""

    trigger = scheduler.db.triggers.create(
        name="message-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(event_script_path),
        event_names=["message_created"],
    )

    now = utcnow()
    events = create_test_events(scheduler.db, now)  # noqa: F841

    matching_events = scheduler.db.events.get_events_for_trigger(
        trigger, is_consumed=False
    )
    scheduler.execute_trigger(trigger, matching_events)

    summary = read_script_output(script_summary_file)
    assert summary["events_received"] == 2  # slack_message + discord_message
    assert "message_created" in summary["event_names"]
    assert "dm_sent" not in summary["event_names"]
    assert "slack" in summary["event_sources"]
    assert "discord" in summary["event_sources"]


def test_execute_trigger_event_source_filtering(
    scheduler: Scheduler,
    event_script_path: Path,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """Integration test: Event filtering by source"""
    output_dir = tmp_path / "toolbox_test_output"
    summary_file = output_dir / "test_script_output.json"
    monkeypatch.setenv("TEST_SCRIPT_OUTPUT_FILE", str(summary_file))

    trigger = scheduler.db.triggers.create(
        name="slack-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(event_script_path),
        event_sources=["slack"],
    )

    now = utcnow()
    slack_event = scheduler.db.events.create(  # noqa: F841
        name="message_created", source="slack", data={"text": "slack"}, timestamp=now
    )
    discord_event = scheduler.db.events.create(  # noqa: F841
        name="message_created",
        source="discord",
        data={"text": "discord"},
        timestamp=now,
    )

    if summary_file.exists():
        summary_file.unlink()

    matching_events = scheduler.db.events.get_events_for_trigger(
        trigger, is_consumed=False
    )
    scheduler.execute_trigger(trigger, matching_events)

    assert summary_file.exists()
    with open(summary_file, "r") as f:
        summary = json.load(f)

    assert summary["events_received"] == 1
    assert "message_created" in summary["event_names"]
    assert "slack" in summary["event_sources"]
    assert "discord" not in summary["event_sources"]


def test_execute_trigger_combined_filtering(
    scheduler: Scheduler,
    event_script_path: Path,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """Integration test: Event filtering by name AND source"""
    output_dir = tmp_path / "toolbox_test_output"
    summary_file = output_dir / "test_script_output.json"
    monkeypatch.setenv("TEST_SCRIPT_OUTPUT_FILE", str(summary_file))

    trigger = scheduler.db.triggers.create(
        name="specific-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(event_script_path),
        event_names=["message_created"],
        event_sources=["slack"],
    )

    now = utcnow()
    slack_message = scheduler.db.events.create(  # noqa: F841
        name="message_created", source="slack", data={"text": "hello"}, timestamp=now
    )
    discord_message = scheduler.db.events.create(  # noqa: F841
        name="message_created", source="discord", data={"text": "hello"}, timestamp=now
    )
    slack_dm = scheduler.db.events.create(  # noqa: F841
        name="dm_sent", source="slack", data={"text": "private"}, timestamp=now
    )

    if summary_file.exists():
        summary_file.unlink()

    matching_events = scheduler.db.events.get_events_for_trigger(
        trigger, is_consumed=False
    )
    scheduler.execute_trigger(trigger, matching_events)

    assert summary_file.exists()
    with open(summary_file, "r") as f:
        summary = json.load(f)

    assert summary["events_received"] == 1  # Only slack message_created
    assert summary["event_names"] == ["message_created"]
    assert summary["event_sources"] == ["slack"]
