from typing import Any

from toolbox_events.events.models import Event
from toolbox_events.events.sinks.memory_sink import MemorySink
from toolbox_events.events.sources.base import EventSource


class MemorySource(EventSource):
    """In-memory event source for testing and development."""

    kind = "memory"

    def __init__(self, sink: MemorySink | None = None, **kwargs: Any):
        """Sink is added to MemorySource to allow for simple testing."""
        if sink is None:
            sink = MemorySink()
        self.sink = sink
        self.events = sink.events

    def get_events(self) -> list[Event]:
        """Get all available events and clear the queue."""
        events = self.events.copy()
        self.events.clear()
        return events
