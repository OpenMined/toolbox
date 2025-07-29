import json
import sqlite3
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MatchedContact(BaseModel):
    query: str
    name: str
    score: float
    channel_id: str


class NamesMatchResponse(BaseModel):
    matches_in_favourites: list[MatchedContact]
    matches_in_all: list[MatchedContact]


def load_json_or_none(data: dict, key: str) -> list[dict] | None:
    if data[key] is None:
        return None
    return json.loads(data[key])


class Chunk(BaseModel):
    chunk_id: UUID
    channel_ids: list[str]
    tss: list[str]
    chunk_text: str
    embedding: Optional[list[float]] = None


class SlackMessage(BaseModel):
    channel_id: str
    user: str
    type: str
    ts: str
    text: str
    reply_count: int | None
    reply_users: list[str] | None
    reply_users_count: int | None
    latest_reply: str | None
    is_locked: bool | None
    subscribed: bool | None
    client_msg_id: str | None
    team: str | None
    parent_user_id: str | None
    thread_ts: str | None
    blocks: list[dict] | None
    reactions: list[dict] | None
    attachments: list[dict] | None

    @classmethod
    def from_sqlite_row(cls, data: sqlite3.Row) -> "SlackMessage":
        data = dict(data)
        data["reply_users"] = load_json_or_none(data, "reply_users")
        data["blocks"] = load_json_or_none(data, "blocks")
        data["reactions"] = load_json_or_none(data, "reactions")
        data["attachments"] = load_json_or_none(data, "attachments")
        return cls(**data)


class ChunkWithMessages(Chunk):
    messages: list[SlackMessage]
