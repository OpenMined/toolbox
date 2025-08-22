import time
from typing import Any, ClassVar

from toolbox_events.daemon.http_client import DaemonClient
from toolbox_events.events.models import Event
from toolbox_events.events.sinks.base import EventSink


class HttpSink(EventSink):
    """Event sink that sends events to a daemon via HTTP with batching."""

    kind: ClassVar[str] = "http"

    def __init__(
        self,
        daemon_url: str = "http://localhost:8000",
        batch_size: int = 10,
        batch_timeout: float = 5.0,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.daemon_url = daemon_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.headers = headers or {}
        self._client: DaemonClient | None = None
        self._batch: list[Event] = []

        self.batch_timeout = batch_timeout
        self.last_flush_time = time.time()

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
        """Flush remaining events and close."""
        self.flush()
        if self._client and hasattr(self._client.conn, "close"):
            self._client.conn.close()

    def flush(self) -> None:
        """Send all batched events to daemon."""
        if not self._batch:
            return
        self.client.send_events(self._batch)
        self._batch = []
        self.last_flush_time = time.time()

    def _should_flush(self) -> bool:
        return (
            len(self._batch) >= self.batch_size
            or time.time() - self.last_flush_time >= self.batch_timeout
        )

    def _send(self, event: Event) -> None:
        """Add event to batch and flush if batch is full."""
        self._batch.append(event)

        if self._should_flush():
            self.flush()
