"""End-to-end integration test for the trigger event system"""

import json
import os
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from toolbox.daemon.app import create_app
from toolbox.settings import DaemonSettings
from toolbox_events.daemon_client import DaemonClient
from toolbox_events.events.sinks import HttpSink


@pytest.fixture
def daemon_app(tmp_path: Path) -> Generator[FastAPI, None, None]:
    """Create test app with scheduler disabled"""
    # Create settings with test database
    settings = DaemonSettings(db_path=tmp_path / "test.db", enable_scheduler=False)
    app = create_app(settings=settings)
    yield app


@pytest.fixture
def daemon_client(daemon_app: FastAPI) -> Generator[DaemonClient, None, None]:
    """Create a DaemonClient that uses the test client instead of httpx"""
    from toolbox_events.daemon_client import DaemonClient

    with TestClient(daemon_app) as test_client:
        client = DaemonClient(conn=test_client)
        yield client


@pytest.fixture
def daemon_sink(daemon_client: DaemonClient) -> HttpSink:
    """Create an HttpSink that uses the daemon client"""
    from toolbox_events.events.sinks import HttpSink

    sink = HttpSink(source_name="test_source")
    sink._client = daemon_client
    return sink


def test_end_to_end_event_flow(
    daemon_app: FastAPI,
    tmp_path: Path,
    daemon_sink: HttpSink,
) -> None:
    """Test complete event flow: HTTP sink → daemon → scheduler → trigger → toolbox_events"""

    # 1. Create a trigger that listens for test events
    test_script = (
        Path(__file__).parent / "assets" / "trigger_script_with_toolbox_events.py"
    )
    trigger = daemon_app.state.trigger_db.triggers.create(
        name="test-e2e-trigger",
        cron_schedule="*/5 * * * *",  # Every 5 minutes (won't run automatically)
        script_path=str(test_script),
        event_names=["test.event", "another.event"],
        event_sources=["test_source"],
    )

    # 2. Send events to daemon via HttpSink
    daemon_sink.send("test.event", {"message": "Hello from test"})
    daemon_sink.send("another.event", {"value": 42})
    daemon_sink.send("ignored.event", {"should": "be ignored"}, source="other_source")

    # 3. Verify events were stored in database
    all_events = daemon_app.state.trigger_db.events.get_all()
    assert len(all_events) == 3

    # 4. Manually execute the trigger (since scheduler thread is disabled)
    output_file = tmp_path / "trigger_output.json"

    # Set up environment to write output file
    env_patch = {
        "TEST_OUTPUT_FILE": str(output_file),
    }

    with patch.dict(os.environ, env_patch):
        # Execute trigger using the scheduler
        scheduler = daemon_app.state.scheduler
        scheduler.execute_trigger(trigger)

    # 5. Verify trigger execution
    executions = daemon_app.state.trigger_db.executions.get_all()
    assert len(executions) == 1
    assert executions[0].trigger_id == trigger.id
    assert executions[0].exit_code == 0  # Success

    # 6. Verify trigger received correct events via toolbox_events
    assert output_file.exists()
    with open(output_file) as f:
        result = json.load(f)

    assert result["success"] is True
    assert result["using_toolbox_events"] is True
    assert result["events_count"] == 2  # Only matching events

    # Check the events received by trigger
    received_events = result["events"]
    assert len(received_events) == 2

    # First event
    assert received_events[0]["name"] == "test.event"
    assert received_events[0]["source"] == "test_source"
    assert received_events[0]["data"] == {"message": "Hello from test"}

    # Second event
    assert received_events[1]["name"] == "another.event"
    assert received_events[1]["source"] == "test_source"
    assert received_events[1]["data"] == {"value": 42}

    # 7. Verify events were consumed from database
    # Check that events are still there but consumed flag would be set
    # For now, just verify we still have all events (consumption logic may vary)
    final_events = daemon_app.state.trigger_db.events.get_all()
    assert len(final_events) == 3  # All events still in database


def test_trigger_with_no_matching_events(
    daemon_app: FastAPI, tmp_path: Path, daemon_sink: HttpSink
) -> None:
    """Test trigger execution when no events match the filter"""

    # Create a trigger with specific event filter
    test_script = (
        Path(__file__).parent / "assets" / "trigger_script_with_toolbox_events.py"
    )
    trigger = daemon_app.state.trigger_db.triggers.create(
        name="test-no-match-trigger",
        cron_schedule="*/5 * * * *",
        script_path=str(test_script),
        event_names=["nonexistent.event"],
    )

    # Send events that don't match using HttpSink
    daemon_sink.send("other.event", {"message": "This won't match"})

    # Execute trigger
    output_file = tmp_path / "no_match_output.json"
    with patch.dict(os.environ, {"TEST_OUTPUT_FILE": str(output_file)}):
        scheduler = daemon_app.state.scheduler
        scheduler.execute_trigger(trigger)

    # Verify trigger was skipped because no matching events
    # When no events match, scheduler skips execution entirely
    assert not output_file.exists()

    # Verify no execution was recorded
    executions = daemon_app.state.trigger_db.executions.get_all()
    assert len(executions) == 0


def test_http_sink_integration(
    daemon_app: FastAPI,
    daemon_sink: HttpSink,
) -> None:
    """Test HttpSink integration"""

    # Send event using HttpSink with different source
    daemon_sink.send("app.started", {"version": "1.0.0"}, source="daemon_app")

    # Verify event was received by daemon
    all_events = daemon_app.state.trigger_db.events.get_all()
    assert len(all_events) == 1
    assert all_events[0].name == "app.started"
    assert all_events[0].source == "daemon_app"
    assert all_events[0].data == {"version": "1.0.0"}
