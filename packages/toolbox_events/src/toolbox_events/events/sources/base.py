from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

from loguru import logger
from toolbox_events.config import EventSourceConfig
from toolbox_events.events.models import Event


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
    def from_config(cls, config: EventSourceConfig, **kwargs: Any) -> Self:
        """Create an EventSource instance from configuration."""
        from toolbox_events.events.sources.source_registry import get_source_cls

        source_cls = get_source_cls(config.kind)
        res = source_cls(**config.model_dump(), **kwargs)

        logger.debug(f"{config.kind} EventSource created")
        return res

    @abstractmethod
    def get_events(self) -> list[Event]:
        """Get available events. Always returns a list for batch compatibility."""
        pass
