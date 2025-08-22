from typing import Dict, Type

from toolbox_events.events.sources.base import EventSource
from toolbox_events.events.sources.memory_source import MemorySource
from toolbox_events.events.sources.stdin_source import StdinSource

_SOURCE_REGISTRY: Dict[str, Type[EventSource]] = {}


def register_source(source_cls: Type[EventSource]) -> None:
    """Register a source implementation."""
    _SOURCE_REGISTRY[source_cls.kind] = source_cls


def get_source_cls(name: str) -> Type[EventSource]:
    """Get a source class by name."""
    if name not in _SOURCE_REGISTRY:
        raise ValueError(f"Unknown source type: {name}")
    return _SOURCE_REGISTRY[name]


register_source(MemorySource)
register_source(StdinSource)
