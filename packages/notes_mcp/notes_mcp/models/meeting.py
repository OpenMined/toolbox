from pydantic import BaseModel


class Meeting(BaseModel):
    filename: str
    chunks_ids: list[int]
