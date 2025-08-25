import os
from unittest.mock import patch

from toolbox_events.settings import EventSinkSettings, EventSourceSettings


def test_event_source_settings():
    with patch.dict(os.environ, {"TOOLBOX_EVENTS_SOURCE_KIND": "test_source"}):
        settings = EventSourceSettings()
        assert settings.kind == "test_source"


def test_event_sink_settings():
    with patch.dict(os.environ, {"TOOLBOX_EVENTS_SINK_KIND": "test_sink"}):
        settings = EventSinkSettings()
        assert settings.kind == "test_sink"
