import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, Field, JsonValue, model_validator
from pydantic_settings import BaseSettings

KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
TOOLBOX_DIR = Path.home() / ".toolbox"
DEFAULT_CACHE_PATH = TOOLBOX_DIR / "vector_cache.db"


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


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class StoreConfig(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    embedding_dim: int = 768
    embedding_model: str = "embeddinggemma:300m"
    batch_size: int = 8
    chunk_size: int = 1000
    chunk_overlap: int = 100
    distance_metric: Literal["cosine", "l1", "l2"] = "cosine"


class TBDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    source: str
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    content_hash: str

    chunks: list["RetrievedChunk"] = Field(default_factory=list, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def set_hash_if_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "content" not in data:
                return data
            if "content_hash" not in data:
                data["content_hash"] = hash_content(data["content"])
        return data

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

    @classmethod
    def from_sql_row(cls, row: dict[str, Any] | sqlite3.Row) -> Self:
        """Create a TBDocument instance from a SQL row.

        Args:
            row: Either a dict or a sqlite3.Row object

        Returns:
            A validated TBDocument instance
        """
        if not isinstance(row, dict):
            row_dict = dict(row)
        else:
            row_dict = row.copy()

        if "metadata" in row_dict and isinstance(row_dict["metadata"], str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])

        return cls.model_validate(row_dict)

    def to_sql_dict(self) -> dict[str, Any]:
        """Convert document to a dict suitable for SQL insertion.

        Returns:
            Dict with all fields converted for SQL storage
        """
        doc_dict = self.model_dump()

        for k, v in doc_dict.items():
            if isinstance(v, dict):
                doc_dict[k] = json.dumps(v)
            elif isinstance(v, datetime):
                doc_dict[k] = v.isoformat()

        return doc_dict

    @classmethod
    def schema_extra_columns(cls) -> list[tuple[str, str]]:
        """Return extra columns to add to the documents table.

        Subclasses can override this to add custom columns.

        Returns:
            List of (column_name, column_type) tuples

        Example:
            return [
                ("channel_id", "TEXT"),
                ("user_id", "TEXT"),
                ("timestamp", "DATETIME"),
            ]
        """
        return []

    @classmethod
    def schema_extra(
        cls,
        documents_table: str,
        chunks_table: str,
        embeddings_table: str,
        fts_table: str,
    ) -> list[str]:
        """Return SQL statements for additional schema modifications.

        Subclasses can override this to add indices, constraints, etc.

        Args:
            documents_table: Name of the documents table
            chunks_table: Name of the chunks table
            embeddings_table: Name of the embeddings table
            fts_table: Name of the FTS5 table

        Returns:
            List of SQL statements to execute after base schema creation

        Example:
            return [
                f"CREATE INDEX idx_{documents_table}_channel ON {documents_table}(channel_id)",
                f"CREATE INDEX idx_{documents_table}_user ON {documents_table}(user_id)",
            ]
        """
        return []


class TBDocumentChunk(BaseModel):
    document_id: str
    chunk_idx: int
    chunk_start: int
    chunk_end: int
    created_at: datetime = Field(default_factory=_utcnow)
    content: str
    content_hash: str
    embedding: list[float] | None = None

    @model_validator(mode="before")
    @classmethod
    def set_hash_if_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "content" not in data:
                return data
            if "content_hash" not in data:
                data["content_hash"] = hash_content(data["content"])
        return data

    @model_validator(mode="after")
    def ensure_utc_for_all_datetimes(self) -> Self:
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime):
                setattr(self, field_name, value.astimezone(timezone.utc))
        return self

    @classmethod
    def from_sql_row(cls, row: dict[str, Any] | sqlite3.Row) -> Self:
        """Create a TBDocumentChunk instance from a SQL row.

        Args:
            row: Either a dict or a sqlite3.Row object

        Returns:
            A validated TBDocumentChunk instance
        """
        if not isinstance(row, dict):
            row_dict = dict(row)
        else:
            row_dict = row.copy()

        return cls.model_validate(row_dict)

    def to_sql_dict(self) -> dict[str, Any]:
        """Convert chunk to a dict suitable for SQL insertion.

        Returns:
            Dict with all fields converted for SQL storage, excluding embedding
        """
        # Exclude embedding since it's stored in a separate table
        chunk_dict = self.model_dump(exclude={"embedding"})

        for k, v in chunk_dict.items():
            if isinstance(v, dict):
                chunk_dict[k] = json.dumps(v)
            elif isinstance(v, datetime):
                chunk_dict[k] = v.isoformat()

        return chunk_dict


class RetrievedChunk(TBDocumentChunk):
    distance: float
