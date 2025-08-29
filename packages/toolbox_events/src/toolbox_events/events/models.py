from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(BaseModel):
    """Represents an event in the system."""

    name: str
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=_utcnow)
    source: str | None = None

    @property
    def full_name(self) -> str:
        """The full name of the event."""
        return f"{self.source}.{self.name}"
