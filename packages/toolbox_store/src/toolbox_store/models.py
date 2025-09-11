from datetime import datetime, timezone
from typing import Self
from uuid import uuid4

from pydantic import BaseModel, Field, JsonValue, model_validator
from pydantic_settings import BaseSettings


def _utcnow():
    return datetime.now(tz=timezone.utc)


class StoreConfig(BaseSettings):
    embedding_dim: int = 384
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    batch_size: int = 8
    chunk_size: int = 1000
    chunk_overlap: int = 100


class ToolboxDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    source: str
    created_at: datetime = Field(default_factory=_utcnow)

    # Model configuration
    embeddings: list["ToolboxEmbedding"] = Field(default_factory=list, exclude=True)

    @model_validator(mode="after")
    def ensure_utc_for_all_datetimes(self) -> Self:
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.astimezone(timezone.utc))
        return self


class ToolboxEmbedding(BaseModel):
    document_id: str
    chunk_idx: int
    chunk_start: int
    chunk_end: int
    created_at: datetime = Field(default_factory=_utcnow)
    content: str
    content_hash: str
    embedding: list[float]

    @model_validator(mode="after")
    def ensure_utc_for_all_datetimes(self) -> Self:
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.astimezone(timezone.utc))
        return self
