import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


def json_or_none(x):
    if x is None:
        return None
    return json.dumps(x)


def load_json_or_none(data: dict, key: str) -> Any:
    if data[key] is None:
        return None
    return json.loads(data[key])


def snowflake_to_datetime(snowflake_id: str) -> str:
    """Convert Discord snowflake ID to ISO timestamp"""
    discord_epoch = 1420070400000  # January 1, 2015
    timestamp_ms = (int(snowflake_id) >> 22) + discord_epoch
    return datetime.fromtimestamp(timestamp_ms / 1000).isoformat()


class DiscordGuild(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    banner: Optional[str] = None
    owner_id: Optional[str] = None
    features: Optional[list[str]] = None
    verification_level: Optional[int] = None
    default_message_notifications: Optional[int] = None
    explicit_content_filter: Optional[int] = None
    preferred_locale: Optional[str] = None

    def to_sql_tuple(self) -> tuple:
        return (
            self.id,
            self.name,
            self.icon,
            self.description,
            self.banner,
            self.owner_id,
            json_or_none(self.features),
            self.verification_level,
            self.default_message_notifications,
            self.explicit_content_filter,
            self.preferred_locale,
            snowflake_to_datetime(self.id),
        )

    @classmethod
    def from_sql_row(cls, data: sqlite3.Row) -> "DiscordGuild":
        data = dict(data)
        data["features"] = load_json_or_none(data, "features")
        data.pop("created_at", None)  # Remove the timestamp field
        return cls(**data)


class DiscordChannel(BaseModel):
    id: str
    type: int
    guild_id: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[str] = None
    topic: Optional[str] = None
    position: Optional[int] = None
    rate_limit_per_user: Optional[int] = None
    permission_overwrites: Optional[list[dict]] = None
    nsfw: Optional[bool] = None
    last_message_id: Optional[str] = None

    def to_sql_tuple(self) -> tuple:
        return (
            self.id,
            self.type,
            self.guild_id,
            self.name,
            self.parent_id,
            self.topic,
            self.position,
            self.rate_limit_per_user,
            json_or_none(self.permission_overwrites),
            self.nsfw,
            self.last_message_id,
            snowflake_to_datetime(self.id),
        )

    @classmethod
    def from_sql_row(cls, data: sqlite3.Row) -> "DiscordChannel":
        data = dict(data)
        data["permission_overwrites"] = load_json_or_none(data, "permission_overwrites")
        data.pop("created_at", None)  # Remove the timestamp field
        return cls(**data)


class DiscordUser(BaseModel):
    id: str
    username: str
    discriminator: Optional[str] = None
    avatar: Optional[str] = None
    global_name: Optional[str] = None
    public_flags: Optional[int] = None
    banner: Optional[str] = None
    accent_color: Optional[int] = None

    def to_sql_tuple(self) -> tuple:
        return (
            self.id,
            self.username,
            self.discriminator,
            self.avatar,
            self.global_name,
            self.public_flags,
            self.banner,
            self.accent_color,
            snowflake_to_datetime(self.id),
        )

    @classmethod
    def from_sql_row(cls, data: sqlite3.Row) -> "DiscordUser":
        data = dict(data)
        data.pop("created_at", None)  # Remove the timestamp field
        return cls(**data)


class DiscordMessage(BaseModel):
    id: str
    channel_id: str
    author_id: str  # Only store author ID, not full author object
    content: str
    timestamp: str
    edited_timestamp: Optional[str] = None
    type: int
    pinned: Optional[bool] = None
    mention_everyone: Optional[bool] = None
    tts: Optional[bool] = None
    mentions: Optional[list[dict]] = None
    mention_roles: Optional[list[str]] = None
    attachments: Optional[list[dict]] = None
    embeds: Optional[list[dict]] = None
    components: Optional[list[dict]] = None
    flags: Optional[int] = None

    @classmethod
    def from_discord_api(cls, data: dict) -> "DiscordMessage":
        """Create DiscordMessage from Discord API response"""
        author_id = data.get("author", {}).get("id") if data.get("author") else None
        return cls(
            id=data["id"],
            channel_id=data["channel_id"],
            author_id=author_id,
            content=data.get("content", ""),
            timestamp=data["timestamp"],
            edited_timestamp=data.get("edited_timestamp"),
            type=data["type"],
            pinned=data.get("pinned"),
            mention_everyone=data.get("mention_everyone"),
            tts=data.get("tts"),
            mentions=data.get("mentions"),
            mention_roles=data.get("mention_roles"),
            attachments=data.get("attachments"),
            embeds=data.get("embeds"),
            components=data.get("components"),
            flags=data.get("flags"),
        )

    def to_sql_tuple(self) -> tuple:
        return (
            self.id,
            self.channel_id,
            self.author_id,
            self.content,
            self.timestamp,
            self.edited_timestamp,
            self.type,
            self.pinned,
            self.mention_everyone,
            self.tts,
            json_or_none(self.mentions),
            json_or_none(self.mention_roles),
            json_or_none(self.attachments),
            json_or_none(self.embeds),
            json_or_none(self.components),
            self.flags,
        )

    @classmethod
    def from_sql_row(cls, data: sqlite3.Row) -> "DiscordMessage":
        data = dict(data)
        data["mentions"] = load_json_or_none(data, "mentions")
        data["mention_roles"] = load_json_or_none(data, "mention_roles")
        data["attachments"] = load_json_or_none(data, "attachments")
        data["embeds"] = load_json_or_none(data, "embeds")
        data["components"] = load_json_or_none(data, "components")
        return cls(**data)
