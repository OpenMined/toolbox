import os
from unittest.mock import patch

from toolbox_events.events.sinks import MemorySink
from toolbox_events.events.sources import MemorySource


def test_memory_sink_and_source():
    """Test that memory sink and source work together."""
    # Create a shared sink with source name
    sink = MemorySink(source_name="test_source")
    source = MemorySource(sink=sink)

    # Send some events
    sink.send("test.event", {"value": 42})
    sink.send("another.event", {"name": "hello"})

    # Get events from source
    events = source.get_events()

    # Verify we got the events with source names
    assert len(events) == 2
    assert events[0].name == "test.event"
    assert events[0].data == {"value": 42}
    assert events[0].source == "test_source"
    assert events[0].full_name == "test_source.test.event"

    assert events[1].name == "another.event"
    assert events[1].data == {"name": "hello"}
    assert events[1].source == "test_source"
    assert events[1].full_name == "test_source.another.event"

    # Verify source is now empty
    events_again = source.get_events()
    assert len(events_again) == 0


def test_top_level_api():
    """Test the top-level send/get_events functions."""
    from toolbox_events import get_events, send_event

    env_vars = {
        "TOOLBOX_EVENTS_SINK_KIND": "memory",
        "TOOLBOX_EVENTS_SOURCE_KIND": "memory",
        "TOOLBOX_EVENTS_SINK_SOURCE_NAME": "test_sink",
    }
    with patch.dict(os.environ, env_vars):
        # Send event to sink
        send_event("api.test", {"worked": True})

        # Get events from source
        events = get_events()

        # Verify
        assert len(events) == 1
        assert events[0].name == "api.test"
        assert events[0].data == {"worked": True}
        assert events[0].source == "test_sink"
        assert events[0].full_name == "test_sink.api.test"
