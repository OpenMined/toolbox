from pydantic import BaseModel


class Meeting(BaseModel):
    filename: str
    audio_chunk_ids: list[int]
