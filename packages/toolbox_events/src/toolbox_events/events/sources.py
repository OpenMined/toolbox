import json
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from loguru import logger

from toolbox_events.events.models import Event
from toolbox_events.settings import EventSourceSettings

if TYPE_CHECKING:
    from toolbox_events.events.sinks import MemorySink


class EventSource(ABC):
    """Base class for event sources that receive events from various origins."""

    kind: ClassVar[str]  # Must be defined by implementations

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "kind") or not isinstance(cls.kind, str):
            raise TypeError(
                f"{cls.__name__} must define a 'kind' class variable as a string"
            )

    @classmethod
    def from_config(cls, config: EventSourceSettings, **kwargs: Any) -> "EventSource":
        """Create an EventSource instance from configuration."""
        source_map = {
            "memory": MemorySource,
            "stdin": StdinSource,
        }

        source_cls = source_map.get(config.kind)
        if not source_cls:
            raise ValueError(f"Unknown source type: {config.kind}")

        res = source_cls(**config.model_dump(), **kwargs)
        logger.debug(f"{config.kind} EventSource created")
        return res

    @abstractmethod
    def get_events(self) -> list[Event]:
        """Get available events. Always returns a list for batch compatibility."""
        pass


class MemorySource(EventSource):
    """In-memory event source for testing and development."""

    kind = "memory"

    def __init__(self, sink: "MemorySink | None" = None, **kwargs: Any):
        """Sink is added to MemorySource to allow for simple testing."""
        if sink is None:
            from toolbox_events.events.sinks import MemorySink

            sink = MemorySink()
        self.sink = sink
        self.events = sink.events

    def get_events(self) -> list[Event]:
        """Get all available events and clear the queue."""
        events = self.events.copy()
        self.events.clear()
        return events


class StdinSource(EventSource):
    """Event source that reads events from stdin as JSON."""

    kind = "stdin"

    def __init__(self, **kwargs: Any):
        self._events: list[Event] | None = None

    def get_events(self) -> list[Event]:
        """
        Read events from stdin once and cache them.
        Expected stdin format: {"events": [{"name": "...", "data": {...}, "source": "..."}, ...]}
        """
        if self._events is None:
            logger.debug("Reading events from stdin")
            try:
                stdin_content = sys.stdin.read().strip()
                if not stdin_content:
                    logger.debug("No data available on stdin")
                    self._events = []
                else:
                    data = json.loads(stdin_content)
                    if isinstance(data, dict):
                        events_data = data.get("events", [])
                        self._events = [
                            Event(**event_data) for event_data in events_data
                        ]
                        logger.info(f"Loaded {len(self._events)} events from stdin")
                    else:
                        raise ValueError(
                            "Invalid stdin format: expected JSON object with 'events' key"
                        )
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse events from stdin: {e}") from e

        return self._events
