import json
import sqlite3
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from toolbox_store.utils import hash_content, timezone


def _utcnow():
    return datetime.now(tz=timezone.utc)


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
