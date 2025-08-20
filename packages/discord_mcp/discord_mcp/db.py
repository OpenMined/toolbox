import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import sqlite_vec
from rapidfuzz import process
from sqlite_vec import serialize_float32

from discord_mcp.models import DiscordChannel, DiscordGuild, DiscordMessage, DiscordUser

HOME = Path.home()
DISCORD_MCP_DB_PATH = HOME / ".discord_mcp" / "db.sqlite"
DISCORD_MCP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_TABLE = "message_embeddings_vec"
EMBEDDINGS_LEN = 768


def deserialize_float32(blob: bytes) -> list[float]:
    return np.frombuffer(blob, dtype=np.float32).tolist()


def _get_discord_connection(path: Path = DISCORD_MCP_DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
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

    cursor.execute(
        f"""
            create virtual table if not exists {EMBEDDINGS_TABLE} using vec0(
                sample_embedding float[{EMBEDDINGS_LEN}],
                chunk_text text,
                chunk_id text,
            );
        """
    )
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunk_messages (
        chunk_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        PRIMARY KEY (chunk_id, message_id),
        FOREIGN KEY (message_id) REFERENCES messages(id)
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


def get_messages_from_channel(
    conn, channel_id: str, n_days_old: int
) -> list[DiscordMessage]:
    """Get messages from a specific channel within the last n days"""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=n_days_old)).isoformat()

    cursor.execute(
        """
        SELECT * FROM messages 
        WHERE channel_id = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """,
        (channel_id, cutoff_date),
    )

    return [DiscordMessage.from_sql_row(row) for row in cursor.fetchall()]


def get_messages_from_dm(conn, author_id: str, n_days_old: int) -> list[DiscordMessage]:
    """Get messages from DMs with a specific user within the last n days"""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=n_days_old)).isoformat()

    cursor.execute(
        """
        SELECT m.* FROM messages m
        JOIN channels c ON m.channel_id = c.id
        WHERE c.type = 1 AND m.author_id = ? AND m.timestamp >= ?
        ORDER BY m.timestamp DESC
    """,
        (author_id, cutoff_date),
    )

    return [DiscordMessage.from_sql_row(row) for row in cursor.fetchall()]


def get_messages_from_all_channels(
    conn, n_days_old: int, limit: int = -1
) -> list[DiscordMessage]:
    """Get messages from all channels within the last n days"""
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=n_days_old)).isoformat()

    cursor.execute(
        """
        SELECT * FROM messages 
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT ?
    """,
        (cutoff_date, limit),
    )

    return [DiscordMessage.from_sql_row(row) for row in cursor.fetchall()]


def get_channels(conn) -> list[DiscordChannel]:
    """Get all channels"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels ORDER BY name")
    return [DiscordChannel.from_sql_row(row) for row in cursor.fetchall()]


def get_users(conn) -> list[DiscordUser]:
    """Get all users"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY username")
    return [DiscordUser.from_sql_row(row) for row in cursor.fetchall()]


def get_user_id_for_name(conn, query: str, top_n: int = 5) -> list[dict]:
    """Get user or channel ID for a name using fuzzy matching (similar to slack mcp)"""
    cursor = conn.cursor()

    # Get all users and channels for matching
    cursor.execute("SELECT id, username, global_name FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT id, name FROM channels WHERE name IS NOT NULL")
    channels = cursor.fetchall()

    # Build name to ID mapping like in slack MCP
    name_to_id = {}
    all_names = []

    # Add users (both username and global_name if available)
    for user in users:
        user_dict = dict(user)
        username = user_dict.get("username", "")
        global_name = user_dict.get("global_name", "")

        if username:
            name_to_id[username] = {"id": user_dict["id"], "type": "user"}
            all_names.append(username)

        if global_name and global_name != username:
            name_to_id[global_name] = {"id": user_dict["id"], "type": "user"}
            all_names.append(global_name)

    # Add channels
    for channel in channels:
        channel_dict = dict(channel)
        channel_name = channel_dict.get("name", "")

        if channel_name:
            name_to_id[channel_name] = {"id": channel_dict["id"], "type": "channel"}
            all_names.append(channel_name)

    # Use rapidfuzz to find matches like in slack MCP
    matches = process.extract(query, all_names, limit=top_n)

    # Format results
    result = []
    for name, score, _ in matches:
        match_info = name_to_id[name]
        result.append(
            {
                "query": query,
                "name": name,
                "score": score,
                "id": match_info["id"],
                "type": match_info["type"],
            }
        )

    return result


def get_messages_without_embeddings(conn, limit=10):
    """Get messages that don't have embeddings yet"""
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT messages.*
    FROM messages
    LEFT JOIN chunk_messages ON messages.id = chunk_messages.message_id
    WHERE chunk_messages.chunk_id IS NULL
    LIMIT ?
    """,
        (limit,),
    )
    return [DiscordMessage.from_sql_row(msg) for msg in cursor.fetchall()]


def get_latest_message_timestamp(conn):
    """Get the timestamp of the latest message for rate limiting"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) AS max_timestamp FROM messages")
    result = cursor.fetchone()
    return result[0] if result[0] else None


def upsert_chunks(conn, chunks):
    """Insert or update chunks with embeddings"""
    for chunk in chunks:
        if chunk.get("embedding") is None:
            raise ValueError("Chunk embedding is required")

    cursor = conn.cursor()
    cursor.executemany(
        f"""
    INSERT OR REPLACE INTO {EMBEDDINGS_TABLE} (chunk_id, sample_embedding, chunk_text)
    VALUES (?, ?, ?)
    """,
        [
            (
                chunk["chunk_id"],
                serialize_float32(chunk["embedding"]),
                chunk["chunk_text"],
            )
            for chunk in chunks
        ],
    )
    cursor.executemany(
        """
    INSERT OR REPLACE INTO chunk_messages (chunk_id, message_id)
    VALUES (?, ?)
    """,
        [
            (chunk["chunk_id"], message_id)
            for chunk in chunks
            for message_id in chunk["message_ids"]
        ],
    )
    conn.commit()


def get_matching_chunks(conn, query_embedding: list[float], limit=10):
    """Get chunks matching the query embedding"""
    cursor = conn.cursor()
    cursor.execute(
        f"""
    SELECT chunks.chunk_id, chunks.chunk_text, chunks.sample_embedding as embedding, chunk_messages.message_id
    FROM (
    SELECT * FROM {EMBEDDINGS_TABLE} WHERE sample_embedding match ?
    ORDER BY distance
    LIMIT ?
    ) as chunks
    JOIN chunk_messages ON chunks.chunk_id = chunk_messages.chunk_id
    """,
        (serialize_float32(query_embedding), limit),
    )
    all_rows = cursor.fetchall()
    rows_for_chunk = defaultdict(list)
    for row in all_rows:
        rows_for_chunk[row["chunk_id"]].append(row)

    res = []
    for chunk_id, rows in rows_for_chunk.items():
        chunk = {
            "chunk_id": chunk_id,
            "message_ids": [row["message_id"] for row in rows],
            "chunk_text": rows[0]["chunk_text"],
            "embedding": deserialize_float32(rows[0]["embedding"]),
        }
        res.append(chunk)

    return res


def get_chunk_messages(conn, chunks):
    """Get full message details for chunks"""
    cursor = conn.cursor()
    res = []
    for chunk in chunks:
        placeholders = ",".join(["?"] * len(chunk["message_ids"]))
        cursor.execute(
            f"""
        SELECT * FROM messages WHERE id IN ({placeholders})
        """,
            chunk["message_ids"],
        )
        messages = [DiscordMessage.from_sql_row(msg) for msg in cursor.fetchall()]
        chunk_with_messages = {
            "chunk_id": chunk["chunk_id"],
            "message_ids": chunk["message_ids"],
            "chunk_text": chunk["chunk_text"],
            "messages": messages,
        }
        res.append(chunk_with_messages)
    return res
