import os
from unittest.mock import patch

from toolbox_events.config import EventSinkConfig, EventSourceConfig


def test_event_source_config():
    with patch.dict(os.environ, {"TOOLBOX_EVENTS_SOURCE_KIND": "test_source"}):
        config = EventSourceConfig()
        assert config.kind == "test_source"


def test_event_sink_config():
    with patch.dict(os.environ, {"TOOLBOX_EVENTS_SINK_KIND": "test_sink"}):
        config = EventSinkConfig()
        assert config.kind == "test_sink"
