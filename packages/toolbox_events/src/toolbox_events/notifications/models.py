from typing import Optional

from pydantic import BaseModel


class Notification(BaseModel):
    message: str
    topic: str
    title: Optional[str] = None
    priority: int = 3  # 1=min, 2=low, 3=default, 4=high, 5=urgent
    tags: Optional[list[str]] = None
