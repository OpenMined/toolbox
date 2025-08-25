from typing import Any

from toolbox_events.events.models import Event
from toolbox_events.events.sinks import EventSink
from toolbox_events.events.sources import EventSource
from toolbox_events.settings import EventSinkSettings, EventSourceSettings

# Global lazy-initialized instances
_default_event_sink: EventSink | None = None
_default_event_source: EventSource | None = None


def get_default_event_sink() -> EventSink:
    """Get or create the default event sink."""
    global _default_event_sink
    if _default_event_sink is None:
        config = EventSinkSettings()
        _default_event_sink = EventSink.from_config(config)
    return _default_event_sink


def get_default_event_source() -> EventSource:
    """Get or create the default event source."""
    global _default_event_source
    if _default_event_source is None:
        config = EventSourceSettings()

        # For development: link sink and source if they are both in-memory
        if config.kind == "memory":
            sink = get_default_event_sink()
            kwargs = {"sink": sink} if sink.kind == "memory" else {}
        else:
            kwargs = {}

        _default_event_source = EventSource.from_config(config, **kwargs)

    return _default_event_source


def send_event(
    name: str,
    data: dict[str, Any],
    source: str | None = None,
) -> None:
    """Send an event using the default event sink."""
    sink = get_default_event_sink()
    sink.send(name, data, source)


def get_events() -> list[Event]:
    """Get events using the default event source."""
    source = get_default_event_source()
    return source.get_events()
