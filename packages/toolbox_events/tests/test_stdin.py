import io
import json
from unittest.mock import patch

import pytest
from toolbox_events.events.sinks import MemorySink
from toolbox_events.events.sources import StdinSource


def test_stdin_source_events():
    """Test StdinSource with single and multiple events."""
    # Single event
    sink = MemorySink(source_name="test_source")
    sink.send("test.event", {"value": 42})

    event_data = sink.events[0].model_dump(mode="json")
    stdin_input = json.dumps({"events": [event_data]})

    with patch("sys.stdin", io.StringIO(stdin_input)):
        source = StdinSource()
        events = source.get_events()

    assert len(events) == 1
    assert events[0].name == "test.event"
    assert events[0].data == {"value": 42}
    assert events[0].source == "test_source"

    # Multiple events
    sink = MemorySink(source_name="test_source")
    sink.send("event.one", {"a": 1})
    sink.send("event.two", {"b": 2})

    events_json = [event.model_dump(mode="json") for event in sink.events]
    stdin_input = json.dumps({"events": events_json})

    with patch("sys.stdin", io.StringIO(stdin_input)):
        source = StdinSource()
        events = source.get_events()

    assert len(events) == 2
    assert events[0].name == "event.one"
    assert events[0].data == {"a": 1}
    assert events[1].name == "event.two"
    assert events[1].data == {"b": 2}


def test_stdin_source_caches_events():
    """Test that StdinSource caches events and doesn't re-read stdin."""
    # Create event using memory sink
    sink = MemorySink(source_name="test_source")
    sink.send("test.event", {})

    # Serialize in new format
    event_data = sink.events[0].model_dump(mode="json")
    stdin_input = json.dumps({"events": [event_data]})

    with patch("sys.stdin", io.StringIO(stdin_input)):
        source = StdinSource()

        # First call reads from stdin
        events1 = source.get_events()
        # Second call returns cached events
        events2 = source.get_events()

    assert len(events1) == 1
    assert len(events2) == 1
    assert events1[0].name == events2[0].name
    assert events1[0].source == events2[0].source


def test_stdin_source_edge_cases():
    """Test StdinSource with empty stdin and invalid inputs."""
    # Empty stdin
    with patch("sys.stdin", io.StringIO("")):
        source = StdinSource()
        events = source.get_events()
        assert len(events) == 0

    # Invalid JSON
    with patch("sys.stdin", io.StringIO("{ invalid json")):
        source = StdinSource()
        with pytest.raises(ValueError):
            source.get_events()

    # Invalid format - should be {"events": [...]}
    invalid_format = json.dumps([{"name": "test", "data": {}}])
    with patch("sys.stdin", io.StringIO(invalid_format)):
        source = StdinSource()
        with pytest.raises(ValueError, match="Invalid stdin format"):
            source.get_events()


def test_stdin_source_from_config():
    """Test StdinSource can be created from config."""
    from toolbox_events.config import EventSourceConfig
    from toolbox_events.events.sources import EventSource

    config = EventSourceConfig(kind="stdin")
    source = EventSource.from_config(config)

    assert isinstance(source, StdinSource)
    assert source.kind == "stdin"
