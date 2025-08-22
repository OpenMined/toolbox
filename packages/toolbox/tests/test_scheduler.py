import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB, utcnow


@pytest.fixture
def db():
    """Create an in-memory test database"""
    return TriggerDB.from_url("sqlite:///:memory:")


@pytest.fixture
def scheduler(db):
    """Create a scheduler with test database"""
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = Path(temp_dir) / "test_scheduler.pid"
        yield Scheduler(db, pid_file)


@pytest.fixture
def test_script_path():
    """Path to the test script for integration tests"""
    script_path = Path(__file__).parent / "assets" / "test_event_script.py"
    assert script_path.exists(), f"Test script not found: {script_path}"
    return script_path


@pytest.fixture
def script_summary_file(tmp_path, monkeypatch):
    """Manages test output file cleanup with unique paths per test"""
    summary_file = tmp_path / "test_script_output.json"
    # Set environment variable so the test script knows where to write
    monkeypatch.setenv("TEST_SCRIPT_OUTPUT_FILE", str(summary_file))
    yield summary_file
    # tmp_path and monkeypatch automatically clean up after test


def read_script_output(summary_file: Path) -> dict:
    """Helper to read and parse script output"""
    assert summary_file.exists(), "Script should have created summary file"
    with open(summary_file, "r") as f:
        return json.load(f)


def create_test_events(db, now):
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


def test_scheduler_finds_due_triggers(scheduler):
    """Test scheduler gets due triggers from database efficiently"""
    now = utcnow()

    # Create a due trigger (past next_run_at)
    due_trigger = scheduler.db.triggers.create(
        name="due-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )
    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        due_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Create a future trigger (not due)
    scheduler.db.triggers.create(
        name="future-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )

    # Test _process_triggers submits only due triggers
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor, now)

    # Should submit only the due trigger to executor
    mock_executor.submit.assert_called_once()
    call_args = mock_executor.submit.call_args[0]
    assert call_args[0] == scheduler.execute_from_scheduler
    assert call_args[1].id == due_trigger.id


def test_scheduler_updates_next_run_before_execution(scheduler):
    """Test execute_from_scheduler updates next_run_at first"""
    import time

    trigger = scheduler.db.triggers.create(
        name="test-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )

    # Small delay to ensure different next_run_at calculation
    time.sleep(0.1)

    with patch.object(scheduler, "execute_trigger") as mock_execute:
        scheduler.execute_from_scheduler(trigger)

        # Verify next_run_at was updated
        updated_trigger = scheduler.db.triggers.get(trigger.id)
        assert updated_trigger.next_run_at is not None

        # Verify execute_trigger was called
        mock_execute.assert_called_once_with(trigger, None, False)


def test_scheduler_handles_event_based_triggers(scheduler):
    """Test scheduler processes event-based triggers correctly"""
    now = utcnow()

    # Create event-based trigger
    event_trigger = scheduler.db.triggers.create(
        name="event-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["test_event"],
    )
    # Set as due
    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        event_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Create matching event
    event = scheduler.db.events.create(
        name="test_event", source="test_source", data={"key": "value"}, timestamp=now
    )

    # Test _process_triggers submits event-based trigger with events
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor, now)

    # Should submit the event trigger to executor with events
    mock_executor.submit.assert_called_once()
    call_args = mock_executor.submit.call_args[0]
    assert call_args[0] == scheduler.execute_from_scheduler
    assert call_args[1].id == event_trigger.id
    assert len(call_args[2]) == 1  # Should have 1 event
    assert call_args[2][0].id == event.id


def test_scheduler_skips_triggers_with_no_events(scheduler):
    """Test scheduler skips event triggers when no events available"""
    now = utcnow()

    # Create event-based trigger with no matching events
    event_trigger = scheduler.db.triggers.create(
        name="event-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["nonexistent_event"],
    )
    # Set as due
    past_time = now - timedelta(minutes=1)
    scheduler.db.triggers.update_next_run_time(
        event_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Test _process_triggers skips triggers with no events
    mock_executor = Mock()
    scheduler._process_triggers(mock_executor, now)

    # Should not submit anything to executor
    mock_executor.submit.assert_not_called()


def test_execute_trigger_creates_execution_record(scheduler):
    """Test execute_trigger creates database execution record"""
    trigger = scheduler.db.triggers.create(
        name="test-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        scheduler.execute_trigger(trigger)

        # Verify execution record was created
        executions = scheduler.db.executions.get_all(trigger_id=trigger.id)
        assert len(executions) == 1
        assert executions[0].trigger_id == trigger.id


def test_execute_from_scheduler_updates_next_run_time(scheduler):
    """Test execute_from_scheduler method updates next_run_at"""
    import time

    trigger = scheduler.db.triggers.create(
        name="test-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )

    # Small delay to ensure different next_run_at calculation
    time.sleep(0.1)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        scheduler.execute_from_scheduler(trigger)

        # Verify next_run_at was updated
        updated_trigger = scheduler.db.triggers.get(trigger.id)
        assert updated_trigger.next_run_at is not None


def test_execute_trigger_does_not_update_next_run_time(scheduler):
    """Test execute_trigger (CLI method) doesn't affect scheduling"""
    trigger = scheduler.db.triggers.create(
        name="test-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )
    original_next_run = trigger.next_run_at

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        scheduler.execute_trigger(trigger)

        # Verify next_run_at was NOT updated
        updated_trigger = scheduler.db.triggers.get(trigger.id)
        assert updated_trigger.next_run_at == original_next_run


def test_scheduler_writes_pid_file(scheduler):
    """Test scheduler writes PID file"""
    assert not scheduler.pid_file.exists()

    scheduler._write_pid_file()

    assert scheduler.pid_file.exists()
    with open(scheduler.pid_file, "r") as f:
        pid = int(f.read().strip())
    assert pid > 0


def test_scheduler_detects_already_running(scheduler):
    """Test scheduler detects if already running"""
    # Initially not running
    assert not scheduler.is_running()

    # Write PID file
    scheduler._write_pid_file()

    # Should detect as running
    assert scheduler.is_running()

    # Clean up
    scheduler._remove_pid_file()
    assert not scheduler.is_running()


def test_execute_trigger_with_actual_script(
    scheduler, test_script_path, script_summary_file
):
    """Integration test: Basic script execution and event passing"""
    now = utcnow()

    # Create test events
    slack_event = scheduler.db.events.create(
        name="test_event",
        source="slack",
        data={"message": "hello world"},
        timestamp=now,
    )
    discord_event = scheduler.db.events.create(
        name="test_event",
        source="discord",
        data={"message": "hello discord"},
        timestamp=now,
    )

    # Create trigger
    trigger = scheduler.db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(test_script_path),
        event_names=["test_event"],
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
    assert slack_event.id in summary["event_ids"]
    assert discord_event.id in summary["event_ids"]


def test_execute_trigger_event_name_filtering(
    scheduler, test_script_path, script_summary_file
):
    """Integration test: Event filtering by name"""
    now = utcnow()
    events = create_test_events(scheduler.db, now)

    # Create trigger that only matches message_created
    trigger = scheduler.db.triggers.create(
        name="message-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(test_script_path),
        event_names=["message_created"],
    )

    matching_events = scheduler.db.events.get_events_for_trigger(
        trigger, is_consumed=False
    )
    scheduler.execute_trigger(trigger, matching_events)

    summary = read_script_output(script_summary_file)
    assert summary["events_received"] == 2  # slack_message + discord_message
    assert events["slack_message"].id in summary["event_ids"]
    assert events["discord_message"].id in summary["event_ids"]
    assert events["slack_dm"].id not in summary["event_ids"]


def test_execute_trigger_event_source_filtering(scheduler):
    """Integration test: Event filtering by source"""
    test_script_path = Path(__file__).parent / "assets" / "test_event_script.py"
    now = utcnow()
    output_dir = Path("/tmp/toolbox_test_output")
    summary_file = output_dir / "test_script_output.json"

    # Create events from different sources
    slack_event = scheduler.db.events.create(
        name="message_created", source="slack", data={"text": "slack"}, timestamp=now
    )
    discord_event = scheduler.db.events.create(
        name="message_created",
        source="discord",
        data={"text": "discord"},
        timestamp=now,
    )

    # Create trigger that only matches slack events
    trigger = scheduler.db.triggers.create(
        name="slack-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(test_script_path),
        event_sources=["slack"],
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
    assert slack_event.id in summary["event_ids"]
    assert discord_event.id not in summary["event_ids"]


def test_execute_trigger_combined_filtering(scheduler):
    """Integration test: Event filtering by name AND source"""
    test_script_path = Path(__file__).parent / "assets" / "test_event_script.py"
    now = utcnow()
    output_dir = Path("/tmp/toolbox_test_output")
    summary_file = output_dir / "test_script_output.json"

    # Create various events
    slack_message = scheduler.db.events.create(
        name="message_created", source="slack", data={"text": "hello"}, timestamp=now
    )
    discord_message = scheduler.db.events.create(
        name="message_created", source="discord", data={"text": "hello"}, timestamp=now
    )
    slack_dm = scheduler.db.events.create(
        name="dm_sent", source="slack", data={"text": "private"}, timestamp=now
    )

    # Create trigger with both name and source filters (AND logic)
    trigger = scheduler.db.triggers.create(
        name="specific-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(test_script_path),
        event_names=["message_created"],
        event_sources=["slack"],
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
    assert slack_message.id in summary["event_ids"]
    assert discord_message.id not in summary["event_ids"]
    assert slack_dm.id not in summary["event_ids"]
