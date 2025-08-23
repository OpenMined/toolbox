import os
from unittest.mock import Mock, patch

from toolbox_events.config import EventSinkConfig
from toolbox_events.events.sinks import HttpSink


def test_http_sink_batching():
    """Test that events are batched and flushed correctly."""
    mock_client = Mock()
    sink = HttpSink(daemon_url="http://test", batch_size=2)
    sink._client = mock_client

    # Send first event - shouldn't flush yet
    sink.send("event.one", {"data": 1})
    mock_client.send_events.assert_not_called()

    # Send second event - should flush batch
    sink.send("event.two", {"data": 2})
    mock_client.send_events.assert_called_once()

    # Verify events were sent
    sent_events = mock_client.send_events.call_args[0][0]
    assert len(sent_events) == 2
    assert sent_events[0].name == "event.one"
    assert sent_events[1].name == "event.two"


def test_http_sink_context_manager():
    """Test HttpSink as context manager flushes on exit."""
    mock_client = Mock()

    with HttpSink(daemon_url="http://test", batch_size=10) as sink:
        sink._client = mock_client
        sink.send("event.test", {"data": "value"})
        # Shouldn't flush yet (batch_size=10)
        mock_client.send_events.assert_not_called()

    # Should flush on context exit
    mock_client.send_events.assert_called_once()
    sent_events = mock_client.send_events.call_args[0][0]
    assert len(sent_events) == 1
    assert sent_events[0].name == "event.test"


def test_http_sink_manual_close():
    """Test manual close flushes remaining events."""
    mock_client = Mock()
    sink = HttpSink(daemon_url="http://test", batch_size=10)
    sink._client = mock_client
    sink.send("event.test", {"data": "value"})

    # Manual close should flush
    sink.close()
    mock_client.send_events.assert_called_once()


def test_http_sink_from_config():
    """Test creating HttpSink from environment configuration."""
    env_vars = {
        "TOOLBOX_EVENTS_SINK_KIND": "http",
        "TOOLBOX_EVENTS_SINK_SOURCE_NAME": "test_source",
        "TOOLBOX_EVENTS_SINK_DAEMON_URL": "https://api.example.com",
        "TOOLBOX_EVENTS_SINK_BATCH_SIZE": "5",
        "TOOLBOX_EVENTS_SINK_BATCH_TIMEOUT": "2.5",
        "TOOLBOX_EVENTS_SINK_TIMEOUT": "15.0",
        "TOOLBOX_EVENTS_SINK_HEADERS": '{"Authorization": "Bearer 12345"}',
    }

    with patch.dict(os.environ, env_vars):
        config = EventSinkConfig()
        sink = HttpSink(**config.model_dump())

        assert sink.source_name == "test_source"
        assert sink.daemon_url == "https://api.example.com"
        assert sink.batch_size == 5
        assert sink.batch_timeout == 2.5
        assert sink.timeout == 15.0
        assert sink.headers == {"Authorization": "Bearer 12345"}
