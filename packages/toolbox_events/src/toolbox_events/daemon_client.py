from typing import Any, Self

import httpx

from toolbox_events.events.models import Event


class DaemonClient:
    def __init__(self, conn: httpx.Client):
        self.conn = conn

    def health(self) -> bool:
        try:
            response = self.conn.get("/v1/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def send_events(self, events: list[Event]) -> None:
        response = self.conn.post(
            "/v1/events/ingest",
            json={"events": [event.model_dump(mode="json") for event in events]},
        )
        response.raise_for_status()

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> Self:
        return cls(httpx.Client(base_url=url, **kwargs))
