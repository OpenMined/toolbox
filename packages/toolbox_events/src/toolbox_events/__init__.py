from typing import Any, Optional

from toolbox_events.events.models import Event
from toolbox_events.events.sinks import EventSink
from toolbox_events.events.sources import EventSource
from toolbox_events.notifications.notifiers import Notifier
from toolbox_events.settings import (
    EventSinkSettings,
    EventSourceSettings,
    NotifierSettings,
)

# Global lazy-initialized instances
_default_event_sink: EventSink | None = None
_default_event_source: EventSource | None = None
_default_notifier: Notifier | None = None


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


def get_default_notifier() -> Notifier:
    """Get or create the default notifier."""
    global _default_notifier
    if _default_notifier is None:
        config = NotifierSettings()
        _default_notifier = Notifier.from_config(config)
    return _default_notifier


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


def notify(
    message: str,
    title: Optional[str] = None,
    priority: int = 3,
    tags: Optional[list[str]] = None,
    topic: Optional[str] = None,
) -> None:
    """Send a notification using the default notifier."""
    notifier = get_default_notifier()
    notifier.notify(message, title, priority, tags, topic)
