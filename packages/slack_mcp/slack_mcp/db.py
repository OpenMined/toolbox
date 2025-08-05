import json
import sqlite3
import struct
import uuid
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import sqlite_vec
from sqlite_vec import serialize_float32

from slack_mcp.models import Chunk, ChunkWithMessages, SlackMessage

HOME = Path.home()
SLACK_MCP_DB_PATH = HOME / ".slack_mcp" / "db.sqlite"
SLACK_MCP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_TABLE = "message_embeddings_vec"
EMBEDDINGS_LEN = 768


def deserialize_float32(blob: bytes) -> list[float]:
    return np.frombuffer(blob, dtype=np.float32).tolist()


def _get_slack_connection():
    conn = sqlite3.connect(SLACK_MCP_DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    create_tables(conn)
    return conn


@contextmanager
def get_slack_connection():
    conn = _get_slack_connection()
    try:
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        channel_id TEXT NOT NULL,
        user TEXT NOT NULL,
        type TEXT NOT NULL,
        ts TEXT NOT NULL,
        text TEXT NOT NULL,
        reply_count INTEGER,
        reply_users TEXT,
        reply_users_count INTEGER,
        latest_reply TEXT,
        is_locked BOOLEAN,
        subscribed BOOLEAN,
        client_msg_id TEXT,
        team TEXT,
        parent_user_id TEXT,
        thread_ts TEXT,
        blocks TEXT,
        reactions TEXT,
        attachments TEXT,
        PRIMARY KEY (channel_id, ts)
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
        channel_id TEXT NOT NULL,
        ts TEXT NOT NULL,
        PRIMARY KEY (chunk_id, channel_id, ts),
        FOREIGN KEY (channel_id, ts) REFERENCES messages(channel_id, ts)
    )
    """)

    conn.commit()


def get_messages_without_embeddings(conn, limit=10):
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT messages.* 
    FROM messages
    LEFT JOIN chunk_messages ON messages.ts = chunk_messages.ts AND messages.channel_id = chunk_messages.channel_id
    WHERE chunk_messages.chunk_id IS NULL
    LIMIT ?
    """,
        (limit,),
    )
    return [SlackMessage.from_sqlite_row(msg) for msg in cursor.fetchall()]


def gather_chunks_without_embeddings(conn, limit=10) -> list[Chunk]:
    messages = get_messages_without_embeddings(conn, limit=limit)
    chunks = []
    for message in messages:
        chunk = Chunk(
            chunk_id=uuid.uuid4(),
            channel_ids=[message.channel_id],
            tss=[message.ts],
            chunk_text=message.text,
        )
        chunks.append(chunk)
    return chunks


def get_matching_chunks(conn, query_embedding: list[float], limit=10) -> list[Chunk]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
    SELECT chunks.chunk_id, chunks.chunk_text, chunks.sample_embedding as embedding, chunk_messages.channel_id, chunk_messages.ts
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
        chunk = Chunk(
            chunk_id=chunk_id,
            channel_ids=[row["channel_id"] for row in rows],
            tss=[row["ts"] for row in rows],
            chunk_text=rows[0]["chunk_text"],
            embedding=deserialize_float32(rows[0]["embedding"]),
        )
        res.append(chunk)

    return res


def get_chunk_messages(conn, chunks: list[Chunk]) -> list[ChunkWithMessages]:
    cursor = conn.cursor()
    res = []
    for chunk in chunks:
        where_clauses = " OR ".join(
            ["(channel_id = ? AND ts = ?)"] * len(chunk.channel_ids)
        )

        cursor.execute(
            f"""
        SELECT * FROM messages WHERE {where_clauses}
        """,
            [single for pair in zip(chunk.channel_ids, chunk.tss) for single in pair],
        )
        messages = [SlackMessage.from_sqlite_row(msg) for msg in cursor.fetchall()]
        chunk_with_messages = ChunkWithMessages(
            chunk_id=chunk.chunk_id,
            channel_ids=chunk.channel_ids,
            tss=chunk.tss,
            chunk_text=chunk.chunk_text,
            messages=messages,
        )
        res.append(chunk_with_messages)
    return res


def upsert_chunks(conn, chunks: list[Chunk]):
    for chunk in chunks:
        if chunk.embedding is None:
            raise ValueError("Chunk embedding is required")

    cursor = conn.cursor()
    cursor.executemany(
        f"""
    INSERT OR REPLACE INTO {EMBEDDINGS_TABLE} (chunk_id, sample_embedding, chunk_text)
    VALUES (?, ?, ?)
    """,
        [
            (
                str(chunk.chunk_id),
                serialize_float32(chunk.embedding),
                chunk.chunk_text,
            )
            for chunk in chunks
        ],
    )
    cursor.executemany(
        """
    INSERT OR REPLACE INTO chunk_messages (chunk_id, channel_id, ts)
    VALUES (?, ?, ?)
    """,
        [
            (str(chunk.chunk_id), channel_id, ts)
            for chunk in chunks
            for channel_id, ts in zip(chunk.channel_ids, chunk.tss)
        ],
    )
    conn.commit()


def get_message(conn, channel_id, ts) -> SlackMessage:
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT * FROM messages WHERE channel_id = ? AND ts = ?
    """,
        (channel_id, ts),
    )
    return SlackMessage.from_sqlite_row(cursor.fetchone())


def upsert_message(conn, message: SlackMessage):
    cursor = conn.cursor()

    def json_or_none(x):
        if x is None:
            return None
        return json.dumps(x)

    cursor.execute(
        """
    INSERT OR REPLACE INTO messages (channel_id, user, type, ts, text, reply_count, reply_users, reply_users_count, latest_reply, is_locked, subscribed, client_msg_id, team, parent_user_id, thread_ts, blocks, reactions, attachments)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            message["channel_id"],
            message["user"],
            message["type"],
            message["ts"],
            message["text"],
            message.get("reply_count", None),
            json_or_none(message.get("reply_users", None)),
            message.get("reply_users_count", None),
            message.get("latest_reply", None),
            message.get("is_locked", None),
            message.get("subscribed", None),
            message.get("client_msg_id", None),
            message.get("team", None),
            message.get("parent_user_id", None),
            message.get("thread_ts", None),
            json_or_none(message.get("blocks", None)),
            json_or_none(message.get("reactions", None)),
            json_or_none(message.get("attachments", None)),
        ),
    )
    conn.commit()


def get_earliest_timestamp_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(CAST(ts AS REAL)) AS min_ts FROM messages;")
    return cursor.fetchone()[0]


def get_latest_timestamp_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(ts AS REAL)) AS max_ts FROM messages;")
    return cursor.fetchone()[0]


def get_n_embeddings(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM message_embeddings_vec")
    return cursor.fetchone()[0]
