from pydantic import BaseModel


class HeartbeatRequest(BaseModel):
    email: str
