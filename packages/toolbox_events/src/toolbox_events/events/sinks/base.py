from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

from loguru import logger
from toolbox_events.config import EventSinkConfig
from toolbox_events.events.models import Event


class EventSink(ABC):
    """Base class for event sinks that send events to various destinations."""

    kind: ClassVar[str]  # Must be defined by implementations

    def __init__(self, source_name: str = "unknown", **kwargs: Any):
        self.source_name = source_name

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "kind") or not isinstance(cls.kind, str):
            raise TypeError(
                f"{cls.__name__} must define a 'kind' class variable as a string"
            )

    @classmethod
    def from_config(cls, config: EventSinkConfig, **kwargs: Any) -> Self:
        """Create an EventSink instance from configuration."""
        from toolbox_events.events.sinks.sink_registry import get_sink_cls

        sink_cls = get_sink_cls(config.kind)
        res = sink_cls(**config.model_dump(), **kwargs)
        logger.debug(f"{config.kind} EventSink created")
        return res

    def send(self, name: str, data: dict[str, Any], source: str | None = None) -> None:
        self._send(Event(name=name, data=data, source=source or self.source_name))

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and flush/close."""
        self.close()

    def close(self) -> None:
        """Close the sink. Called after all events are sent."""
        pass

    def flush(self) -> None:
        """Flush any buffered events."""
        pass

    @abstractmethod
    def _send(self, event: Event) -> None:
        """Send an event to the sink."""
        pass
