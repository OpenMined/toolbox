from typing import Any

from toolbox_events.events.models import Event
from toolbox_events.events.sinks.base import EventSink


class MemorySink(EventSink):
    """In-memory event sink for testing and development."""

    kind = "memory"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.events: list[Event] = []

    def _send(self, event: Event) -> None:
        """Store the event in memory."""
        self.events.append(event)
