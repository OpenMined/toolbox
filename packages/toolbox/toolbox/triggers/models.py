from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Event(BaseModel):
    name: str
    data: dict[str, Any]
    timestamp: datetime
    source: str | None = None
