from abc import ABC, abstractmethod
from typing import Any, ClassVar

from loguru import logger

from toolbox_events.daemon_client import DaemonClient
from toolbox_events.events.models import Event
from toolbox_events.settings import EventSinkSettings


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
    def from_config(cls, config: EventSinkSettings, **kwargs: Any) -> "EventSink":
        """Create an EventSink instance from configuration."""
        sink_map = {
            "memory": MemorySink,
            "http": HttpSink,
        }

        sink_cls = sink_map.get(config.kind)
        if not sink_cls:
            raise ValueError(f"Unknown sink type: {config.kind}")

        res = sink_cls(**config.model_dump(), **kwargs)
        logger.debug(f"{config.kind} EventSink created")
        return res

    def send(self, name: str, data: dict[str, Any], source: str | None = None) -> None:
        try:
            self._send(Event(name=name, data=data, source=source or self.source_name))
        except Exception as e:
            logger.error(f"Error sending event {name}: {e}")

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close."""
        self.close()

    def close(self) -> None:
        """Close the sink. Called after all events are sent."""
        pass

    @abstractmethod
    def _send(self, event: Event) -> None:
        """Send an event to the sink."""
        pass


class MemorySink(EventSink):
    """In-memory event sink for testing and development."""

    kind = "memory"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.events: list[Event] = []

    def _send(self, event: Event) -> None:
        """Store the event in memory."""
        self.events.append(event)


class HttpSink(EventSink):
    """Event sink that sends events to a daemon via HTTP."""

    kind: ClassVar[str] = "http"

    def __init__(
        self,
        daemon_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.daemon_url = daemon_url
        self.timeout = timeout
        self.headers = headers or {}
        self._client: DaemonClient | None = None

    @property
    def client(self) -> DaemonClient:
        if not self._client:
            self._client = DaemonClient.from_url(
                self.daemon_url,
                timeout=self.timeout,
                headers=self.headers,
            )
        return self._client

    def close(self) -> None:
        if self._client and hasattr(self._client.conn, "close"):
            self._client.conn.close()

    def _send(self, event: Event) -> None:
        self.client.send_events([event])
