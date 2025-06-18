import base64
from datetime import datetime
from pathlib import Path
import sqlite3
from time import sleep
from contextlib import contextmanager

from data_syncer.models import AudioChunk, AudioChunkDB
import requests


URL = "http://localhost:8000"
HOME = Path.home()

SQLITE_DB_PATH = HOME / ".data-syncer-mcp" / "data.db"
SCREENPIPE_DATA_DIR = HOME / ".screenpipe" / "data"

SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


file_id_counter = 0

conn = sqlite3.connect(SQLITE_DB_PATH)
conn.row_factory = sqlite3.Row


@contextmanager
def get_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    try:
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synced_files (
            file_name TEXT PRIMARY KEY,
            chunk_id INTEGER
        )
    """)
    conn.commit()


def get_synced_files(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT file_name, chunk_id FROM synced_files")
    return [AudioChunkDB.from_sqlite_row(row) for row in cursor.fetchall()]


def mark_file_as_synced(conn, audio_chunk: AudioChunkDB):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO synced_files (file_name, chunk_id) VALUES (?, ?)",
        (audio_chunk.file_name, audio_chunk.chunk_id),
    )
    conn.commit()


def get_files_to_sync(conn):
    files = list(SCREENPIPE_DATA_DIR.glob("*"))
    files = [f for f in files if "input" in f.name]
    files_to_sync = []
    for file in files:
        if file.name not in get_synced_files(conn):
            files_to_sync.append(file)
    return files_to_sync
