from datetime import datetime
from pydantic import BaseModel
import base64


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
    offset_index: int
    timestamp: str
    transcription: str
    device: str
    is_input_device: bool
    speaker_id: int
    transcription_engine: str
    start_time: float
    end_time: float
    text_length: int

    @property
    def datetime(self):
        return datetime.fromisoformat(self.timestamp)

    @classmethod
    def from_sql_row(cls, row):
        return cls(
            id=row["id"],
            offset_index=row["offset_index"],
            timestamp=row["timestamp"],
            transcription=row["transcription"],
            device=row["device"],
            is_input_device=row["is_input_device"],
            speaker_id=row["speaker_id"],
            transcription_engine=row["transcription_engine"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            text_length=row["text_length"],
        )


class TranscriptionChunksResult(BaseModel):
    transcription_chunks: list[AudioChunk]
    indexed: list[bool]
