import contextlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from notes_mcp.models.audio import AudioChunk
from notes_mcp.models.user import User
from notes_mcp.settings import settings

HOME = Path.home()

NOTES_DB_PATH = HOME / ".meeting-notes-mcp" / "db.sqlite"
NOTES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DEV_EMAIL = "dev@openmined.org"
DEV_ACCESS_TOKEN = "dev_mode"

# Connect to the SQLite database
conn = sqlite3.connect(NOTES_DB_PATH)
conn.row_factory = sqlite3.Row


@contextlib.contextmanager
def get_notes_db():
    try:
        conn = sqlite3.connect(NOTES_DB_PATH)
        conn.row_factory = sqlite3.Row
        create_tables(conn)
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    access_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
""")
    conn.commit()


def insert_user(conn, email: str, access_token: str) -> int:
    """Insert a new user into the database and return the user ID."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO users (email, access_token)
            VALUES (?, ?)
        """,
            (email, access_token),
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        # User already exists, update the access token
        cursor.execute(
            """
            UPDATE users SET access_token = ? WHERE email = ?
        """,
            (access_token, email),
        )
        conn.commit()
        # Get the user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        return cursor.fetchone()["id"]


def get_user_by_email(conn, email: str):
    """Get user by email address."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


def get_user_by_id(conn, user_id: int):
    """Get user by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


def get_users(conn) -> list[User]:
    if settings.create_dev_user:
        return [User(id=1, email=DEV_EMAIL, access_token=DEV_ACCESS_TOKEN)]
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return [User(**dict(row)) for row in cursor.fetchall()]


def set_heartbeat(conn, email: str):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET last_heartbeat = CURRENT_TIMESTAMP WHERE email = ?",
        (email,),
    )
    conn.commit()


def get_heartbeat(conn, email: str):
    cursor = conn.cursor()
    cursor.execute("SELECT last_heartbeat FROM users WHERE email = ?", (email,))
    return cursor.fetchone()["last_heartbeat"]


def active_since(conn, email: str, seconds: int):
    heartbeat_timestamp = get_heartbeat(conn, email)
    heartbeat_datetime = datetime.strptime(
        heartbeat_timestamp, "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    return datetime.now() - heartbeat_datetime > timedelta(seconds=seconds)
