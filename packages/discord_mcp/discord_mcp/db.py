import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from discord_mcp.models import DiscordMessage, DiscordUser, DiscordChannel, DiscordGuild

HOME = Path.home()
DISCORD_MCP_DB_PATH = HOME / ".discord_mcp" / "db.sqlite"
DISCORD_MCP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_discord_connection(path: Path = DISCORD_MCP_DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    return conn


@contextmanager
def get_discord_connection(path: Path = DISCORD_MCP_DB_PATH):
    conn = _get_discord_connection(path)
    try:
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        icon TEXT,
        description TEXT,
        banner TEXT,
        owner_id TEXT,
        features TEXT,
        verification_level INTEGER,
        default_message_notifications INTEGER,
        explicit_content_filter INTEGER,
        preferred_locale TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id TEXT PRIMARY KEY,
        type INTEGER NOT NULL,
        guild_id TEXT,
        name TEXT,
        parent_id TEXT,
        topic TEXT,
        position INTEGER,
        rate_limit_per_user INTEGER,
        permission_overwrites TEXT,
        nsfw BOOLEAN,
        last_message_id TEXT,
        created_at TEXT,
        FOREIGN KEY (guild_id) REFERENCES guilds(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        discriminator TEXT,
        avatar TEXT,
        global_name TEXT,
        public_flags INTEGER,
        banner TEXT,
        accent_color INTEGER,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        author_id TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        edited_timestamp TEXT,
        type INTEGER NOT NULL,
        pinned BOOLEAN,
        mention_everyone BOOLEAN,
        tts BOOLEAN,
        mentions TEXT,
        mention_roles TEXT,
        attachments TEXT,
        embeds TEXT,
        components TEXT,
        flags INTEGER,
        FOREIGN KEY (channel_id) REFERENCES channels(id),
        FOREIGN KEY (author_id) REFERENCES users(id)
    )
    """)

    conn.commit()


def upsert_guild(conn, guild: DiscordGuild):
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO guilds (id, name, icon, description, banner, owner_id, features, verification_level, default_message_notifications, explicit_content_filter, preferred_locale, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        guild.to_sql_tuple(),
    )
    conn.commit()


def upsert_channel(conn, channel: DiscordChannel):
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO channels (id, type, guild_id, name, parent_id, topic, position, rate_limit_per_user, permission_overwrites, nsfw, last_message_id, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        channel.to_sql_tuple(),
    )
    conn.commit()


def upsert_user(conn, user: DiscordUser):
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO users (id, username, discriminator, avatar, global_name, public_flags, banner, accent_color, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        user.to_sql_tuple(),
    )
    conn.commit()


def upsert_message(conn, message: DiscordMessage):
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO messages (id, channel_id, author_id, content, timestamp, edited_timestamp, type, pinned, mention_everyone, tts, mentions, mention_roles, attachments, embeds, components, flags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        message.to_sql_tuple(),
    )
    conn.commit()


def get_earliest_timestamp_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(timestamp) AS min_ts FROM messages;")
    result = cursor.fetchone()
    return result[0] if result[0] else None


def get_latest_timestamp_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) AS max_ts FROM messages;")
    result = cursor.fetchone()
    return result[0] if result[0] else None


def get_message_count(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    return cursor.fetchone()[0]
