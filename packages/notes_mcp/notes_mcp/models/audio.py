import base64
from datetime import datetime

from pydantic import BaseModel


class TranscribeRequest(BaseModel):
    token: str = "dev_key"
    audio_base64_str: str

    @classmethod
    def from_bytes(cls, audio_bytes: bytes, token=None) -> "TranscribeRequest":
        return cls(
            audio_base64_str=base64.b64encode(audio_bytes).decode("utf-8"), token=token
        )

    @property
    def audio_bytes(self) -> bytes:
        return base64.b64decode(self.audio_base64_str)


class TranscriptionStoreRequest(BaseModel):
    transcription: str
    audio_chunk_id: int
    timestamp: str
    user_email: str
    device: str = "MacBook Pro Microphone"


class AudioChunk(BaseModel):
    id: int
    file_path: str
    timestamp: str

    @property
    def datetime(self):
        return datetime.fromisoformat(self.timestamp)


class AudioChunksResult(BaseModel):
    audio_chunks: list[AudioChunk]
    indexed: list[bool]
