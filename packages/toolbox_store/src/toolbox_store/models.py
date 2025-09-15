import re
from datetime import datetime, timezone
from typing import Self
from uuid import uuid4

from pydantic import BaseModel, Field, JsonValue, model_validator
from pydantic_settings import BaseSettings

KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def is_valid_field_identifier(key: str) -> bool:
    """
    Check if a string is a valid field identifier/key.
    ASCII letters, numbers, underscore, dash only.
    """
    if not key or len(key) > 255 or all(c in "-_" for c in key):
        return False
    return bool(KEY_PATTERN.match(key))


def _utcnow():
    return datetime.now(tz=timezone.utc)


class StoreConfig(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    embedding_dim: int = 768
    embedding_model: str = "embeddinggemma:300m"
    batch_size: int = 8
    chunk_size: int = 1000
    chunk_overlap: int = 100


class TBDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    source: str
    created_at: datetime = Field(default_factory=_utcnow)

    chunks: list["RetrievedChunk"] = Field(default_factory=list, exclude=True)

    @model_validator(mode="after")
    def ensure_utc_for_all_datetimes(self) -> Self:
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.astimezone(timezone.utc))
        return self

    @model_validator(mode="after")
    def validate_dict_keys(self) -> Self:
        """Validate all keys in dict fields follow naming rules."""

        def validate_nested_dict(d: dict, path: str = "") -> None:
            for key, value in d.items():
                if not is_valid_field_identifier(key):
                    raise ValueError(
                        f"Invalid key '{key}' at {path or 'root'}. Supported characters: [a-zA-Z0-9_-]"
                    )
                if isinstance(value, dict):
                    validate_nested_dict(value, f"{path}.{key}" if path else key)

        for field_name, field_info in type(self).model_fields.items():
            if field_info.exclude:
                continue
            value = getattr(self, field_name)
            if isinstance(value, dict):
                validate_nested_dict(value, field_name)

        return self


class TBDocumentChunk(BaseModel):
    document_id: str
    chunk_idx: int
    chunk_start: int
    chunk_end: int
    created_at: datetime = Field(default_factory=_utcnow)
    content: str
    content_hash: str
    embedding: list[float] | None

    @model_validator(mode="after")
    def ensure_utc_for_all_datetimes(self) -> Self:
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.astimezone(timezone.utc))
        return self


class RetrievedChunk(TBDocumentChunk):
    distance: float
