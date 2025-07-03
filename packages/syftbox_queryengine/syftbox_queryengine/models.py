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


class HeartbeatEntry(BaseModel):
    app_name: str
    email: str
    url: str
    healthy: bool

    @classmethod
    def from_sqlite_row(cls, row):
        return cls(
            app_name=row["app_name"],
            email=row["email"],
            url=row["url"],
            healthy=row["healthy"],
        )


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
    audio_chunk_ids: list[int]


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

    @classmethod
    def from_sql_row(cls, row):
        return cls(
            id=row["id"],
            file_path=row["file_path"],
            timestamp=row["timestamp"],
        )


class AudioChunksResult(BaseModel):
    audio_chunks: list[AudioChunk]
    indexed: list[bool]
