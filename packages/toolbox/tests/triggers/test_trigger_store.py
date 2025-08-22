from datetime import datetime, timedelta, timezone

import pytest
from toolbox.triggers.trigger_store import TriggerDB, utcnow


@pytest.fixture
def db():
    """Create an in-memory test database"""
    return TriggerDB.from_url("sqlite:///:memory:")


def test_create_trigger_with_cron(db):
    """Test creating a trigger with cron schedule calculates next_run_at"""
    trigger = db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",  # Every 5 minutes
        script_path="/tmp/test.py",
    )

    assert trigger.name == "test-trigger"
    assert trigger.cron_schedule == "*/5 * * * *"
    assert trigger.enabled is True
    assert trigger.next_run_at is not None
    assert trigger.next_run_at > utcnow()


def test_update_trigger_recalculates_next_run(db):
    """Test updating trigger cron schedule recalculates next_run_at"""
    import time

    trigger = db.triggers.create(
        name="test-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )

    # Small delay to ensure different next_run_at calculation
    time.sleep(0.1)

    # Update cron schedule
    db.triggers.update(trigger.id, cron_schedule="*/10 * * * *")

    updated_trigger = db.triggers.get(trigger.id)
    assert updated_trigger.cron_schedule == "*/10 * * * *"
    # With different cron schedule, next_run_at should be recalculated
    assert updated_trigger.next_run_at is not None


def test_get_due_triggers(db):
    """Test get_due_triggers behavior with various trigger states"""
    now = utcnow()

    # Create trigger that should be due (past next_run_at)
    due_trigger = db.triggers.create(
        name="due-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )
    past_time = now - timedelta(minutes=1)
    db.triggers.update_next_run_time(
        due_trigger.id, from_time=past_time - timedelta(minutes=5)
    )

    # Create trigger that should not be due (future next_run_at)
    future_trigger = db.triggers.create(
        name="future-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )
    # next_run_at should be in the future by default

    # Create disabled trigger
    disabled_trigger = db.triggers.create(
        name="disabled-trigger", cron_schedule="*/5 * * * *", script_path="/tmp/test.py"
    )
    db.triggers.update(disabled_trigger.id, enabled=False)

    # Test get_due_triggers
    due_triggers = db.triggers.get_due_triggers(now)
    trigger_ids = [t.id for t in due_triggers]

    # Should include only the due trigger
    assert len(due_triggers) == 1
    assert due_trigger.id in trigger_ids
    assert future_trigger.id not in trigger_ids
    assert disabled_trigger.id not in trigger_ids


def test_next_run_at_scheduling(db):
    """Test next_run_at calculation and updates"""
    # Test calculation on creation
    trigger = db.triggers.create(
        name="test-trigger",
        cron_schedule="0 12 * * *",  # Daily at noon
        script_path="/tmp/test.py",
        enabled=True,
    )

    assert trigger.next_run_at is not None
    assert isinstance(trigger.next_run_at, datetime)
    assert trigger.next_run_at.tzinfo == timezone.utc

    # Test disable sets next_run_at to None
    db.triggers.update(trigger.id, enabled=False)
    disabled_trigger = db.triggers.get(trigger.id)
    assert disabled_trigger.next_run_at is None

    # Test re-enable recalculates next_run_at
    db.triggers.update(trigger.id, enabled=True)
    enabled_trigger = db.triggers.get(trigger.id)
    assert enabled_trigger.next_run_at is not None


def test_invalid_cron_sets_next_run_at_none(db):
    """Test invalid cron schedules raise ValueError"""
    with pytest.raises(ValueError, match="Invalid cron schedule"):
        db.triggers.create(
            name="invalid-trigger",
            cron_schedule="invalid cron",
            script_path="/tmp/test.py",
        )


def test_create_events(db):
    """Test basic event creation and storage"""
    now = utcnow()
    event = db.events.create(
        name="message_created",
        source="slack",
        data={"channel": "general", "user": "alice"},
        timestamp=now,
    )

    assert event.name == "message_created"
    assert event.source == "slack"
    assert event.data == {"channel": "general", "user": "alice"}
    assert event.timestamp == now
    assert event.id is not None


def test_get_events_for_trigger_matching(db):
    """Test event matching logic for triggers"""
    now = utcnow()

    # Create various events
    slack_msg = db.events.create("message_created", "slack", {"text": "hello"}, now)
    discord_msg = db.events.create("message_created", "discord", {"text": "hi"}, now)
    slack_dm = db.events.create("dm_sent", "slack", {"text": "private"}, now)
    obsidian_note = db.events.create("note_created", "obsidian", {"title": "test"}, now)

    # Test trigger with specific event name only
    name_trigger = db.triggers.create(
        name="name-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["message_created"],
    )
    name_events = db.events.get_events_for_trigger(name_trigger, is_consumed=False)
    name_event_ids = [e.id for e in name_events]
    assert slack_msg.id in name_event_ids
    assert discord_msg.id in name_event_ids
    assert slack_dm.id not in name_event_ids
    assert obsidian_note.id not in name_event_ids

    # Test trigger with specific source only
    source_trigger = db.triggers.create(
        name="source-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_sources=["slack"],
    )
    source_events = db.events.get_events_for_trigger(source_trigger, is_consumed=False)
    source_event_ids = [e.id for e in source_events]
    assert slack_msg.id in source_event_ids
    assert slack_dm.id in source_event_ids
    assert discord_msg.id not in source_event_ids
    assert obsidian_note.id not in source_event_ids

    # Test trigger with both name and source filters (AND logic)
    both_trigger = db.triggers.create(
        name="both-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["message_created"],
        event_sources=["slack"],
    )
    both_events = db.events.get_events_for_trigger(both_trigger, is_consumed=False)
    both_event_ids = [e.id for e in both_events]
    assert slack_msg.id in both_event_ids
    assert discord_msg.id not in both_event_ids
    assert slack_dm.id not in both_event_ids

    # Test trigger with no filters (should match all events)
    all_trigger = db.triggers.create(
        name="all-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
    )
    all_events = db.events.get_events_for_trigger(all_trigger, is_consumed=False)
    all_event_ids = [e.id for e in all_events]
    assert len(all_events) == 4  # Should get all events
    assert slack_msg.id in all_event_ids
    assert discord_msg.id in all_event_ids
    assert slack_dm.id in all_event_ids
    assert obsidian_note.id in all_event_ids


def test_get_events_for_trigger_consumption(db):
    """Test event consumption tracking"""
    now = utcnow()

    # Create events and trigger
    event1 = db.events.create("test_event", "test_source", {}, now)
    event2 = db.events.create("test_event", "test_source", {}, now)

    trigger = db.triggers.create(
        name="test-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["test_event"],
    )

    # Initially, both events should be unconsumed
    unconsumed = db.events.get_events_for_trigger(trigger, is_consumed=False)
    assert len(unconsumed) == 2

    consumed = db.events.get_events_for_trigger(trigger, is_consumed=True)
    assert len(consumed) == 0

    # Mark one event as triggered/consumed
    execution = db.executions.create(trigger.id)
    db.events.mark_events_triggered(trigger.id, [event1.id], execution.id)

    # Now should have 1 unconsumed, 1 consumed
    unconsumed = db.events.get_events_for_trigger(trigger, is_consumed=False)
    consumed = db.events.get_events_for_trigger(trigger, is_consumed=True)

    assert len(unconsumed) == 1
    assert unconsumed[0].id == event2.id
    assert len(consumed) == 1
    assert consumed[0].id == event1.id


def test_event_based_trigger_properties(db):
    """Test is_event_based property"""
    # Cron-only trigger
    cron_trigger = db.triggers.create(
        name="cron-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
    )
    assert cron_trigger.is_event_based is False

    # Event name only
    name_trigger = db.triggers.create(
        name="name-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["test_event"],
    )
    assert name_trigger.is_event_based is True

    # Event source only
    source_trigger = db.triggers.create(
        name="source-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_sources=["test_source"],
    )
    assert source_trigger.is_event_based is True

    # Both event name and source
    both_trigger = db.triggers.create(
        name="both-trigger",
        cron_schedule="*/5 * * * *",
        script_path="/tmp/test.py",
        event_names=["test_event"],
        event_sources=["test_source"],
    )
    assert both_trigger.is_event_based is True
