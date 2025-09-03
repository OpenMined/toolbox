import os
from unittest.mock import Mock, patch

from toolbox_events.events.sinks import HttpSink
from toolbox_events.settings import EventSinkSettings


def test_http_sink_immediate_send():
    """Test that events are sent immediately."""
    mock_client = Mock()
    sink = HttpSink(daemon_url="http://test")
    sink._client = mock_client

    # Send event - should send immediately
    sink.send("event.one", {"data": 1})
    mock_client.send_events.assert_called_once()

    # Verify event was sent
    sent_events = mock_client.send_events.call_args[0][0]
    assert len(sent_events) == 1
    assert sent_events[0].name == "event.one"
    assert sent_events[0].data == {"data": 1}


def test_http_sink_multiple_events():
    """Test that multiple events are sent individually."""
    mock_client = Mock()
    sink = HttpSink(daemon_url="http://test")
    sink._client = mock_client

    # Send multiple events
    sink.send("event.one", {"data": 1})
    sink.send("event.two", {"data": 2})

    # Should be called twice (once per event)
    assert mock_client.send_events.call_count == 2

    # Verify each call sent one event
    first_call = mock_client.send_events.call_args_list[0][0][0]
    second_call = mock_client.send_events.call_args_list[1][0][0]

    assert len(first_call) == 1
    assert first_call[0].name == "event.one"

    assert len(second_call) == 1
    assert second_call[0].name == "event.two"


def test_http_sink_context_manager():
    """Test HttpSink as context manager."""
    mock_client = Mock()

    with HttpSink(daemon_url="http://test") as sink:
        sink._client = mock_client
        sink.send("event.test", {"data": "value"})
        # Should send immediately
        mock_client.send_events.assert_called_once()

    # Context manager should call close
    assert mock_client.send_events.call_count == 1


def test_http_sink_from_config():
    """Test creating HttpSink from environment configuration."""
    env_vars = {
        "TOOLBOX_EVENTS_SINK_KIND": "http",
        "TOOLBOX_EVENTS_SINK_SOURCE_NAME": "test_source",
        "TOOLBOX_EVENTS_SINK_DAEMON_URL": "https://api.example.com",
        "TOOLBOX_EVENTS_SINK_TIMEOUT": "15.0",
        "TOOLBOX_EVENTS_SINK_HEADERS": '{"Authorization": "Bearer 12345"}',
    }

    with patch.dict(os.environ, env_vars):
        config = EventSinkSettings()
        sink = HttpSink(**config.model_dump())

        assert sink.source_name == "test_source"
        assert sink.daemon_url == "https://api.example.com"
        assert sink.timeout == 15.0
        assert sink.headers == {"Authorization": "Bearer 12345"}
