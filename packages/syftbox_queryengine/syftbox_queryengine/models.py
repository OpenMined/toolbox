from datetime import datetime

from pydantic import BaseModel


class SubmitResult(BaseModel):
    message: str


class FileToSync(BaseModel):
    filename: str
    chunk_id: int
    encoded_bts: str
    timestamp: str
    device: str
    user_email: str


class AudioChunkDB(BaseModel):
    chunk_id: int
    file_path: str

    @classmethod
    def from_sqlite_row(cls, row):
        return cls(
            chunk_id=row["chunk_id"],
            file_path=row["file_path"],
        )


class FilesToSyncResponse(BaseModel):
    file: FileToSync | None = None


class MeetingModel(BaseModel):
    filename: str
    chunks_ids: list[int]


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
