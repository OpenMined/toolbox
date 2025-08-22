from typing import Dict, Type

from toolbox_events.events.sinks.base import EventSink
from toolbox_events.events.sinks.memory_sink import MemorySink

_SINK_REGISTRY: Dict[str, Type[EventSink]] = {}


def register_sink(sink_cls: Type[EventSink]) -> None:
    """Register a sink implementation."""
    _SINK_REGISTRY[sink_cls.kind] = sink_cls


def get_sink_cls(name: str) -> Type[EventSink]:
    """Get a sink class by name."""
    if name not in _SINK_REGISTRY:
        raise ValueError(f"Unknown sink type: {name}")
    return _SINK_REGISTRY[name]


register_sink(MemorySink)
