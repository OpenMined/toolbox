import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import numpy as np
import sqlite_vec
from toolbox_store import ToolboxStore
from toolbox_store.models import StoreConfig

from .vectorstore_models import Tweet

HOME = Path.home()
TWITTER_MCP_DB_PATH = HOME / ".twitter-mcp" / "db.sqlite"
TWITTER_VECTORSTORE_DB_PATH = HOME / ".twitter-mcp" / "tweet_toolbox_store.db"
TWITTER_MCP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_TABLE = "tweet_embeddings_vec"
EMBEDDINGS_LEN = 768


def deserialize_float32(blob: bytes) -> list[float]:
    return np.frombuffer(blob, dtype=np.float32).tolist()


def get_tweet_store() -> ToolboxStore:
    """Get ToolboxStore instance for tweets"""
    config = StoreConfig()
    store_path = TWITTER_VECTORSTORE_DB_PATH
    return ToolboxStore(
        collection="tweets",
        db_path=str(store_path),
        config=config,
        document_class=Tweet,
    )


def _get_twitter_connection(path: Path = TWITTER_MCP_DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    create_tables(conn)
    return conn


@contextmanager
def get_twitter_connection(path: Path = TWITTER_MCP_DB_PATH):
    conn = _get_twitter_connection(path)
    try:
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        screen_name TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        avatar_url TEXT,
        banner_url TEXT,
        followers_count INTEGER,
        following_count INTEGER,
        statuses_count INTEGER,
        verified BOOLEAN,
        blue_verified BOOLEAN,
        location TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tweets (
        id TEXT PRIMARY KEY,
        author_id TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        conversation_id TEXT,
        in_reply_to_user_id TEXT,
        in_reply_to_status_id TEXT,
        lang TEXT,
        retweet_count INTEGER DEFAULT 0,
        favorite_count INTEGER DEFAULT 0,
        reply_count INTEGER DEFAULT 0,
        quote_count INTEGER DEFAULT 0,
        bookmark_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        is_quote_status BOOLEAN DEFAULT FALSE,
        possibly_sensitive BOOLEAN DEFAULT FALSE,
        retweeted BOOLEAN DEFAULT FALSE,
        favorited BOOLEAN DEFAULT FALSE,
        bookmarked BOOLEAN DEFAULT FALSE,
        note_tweet_text TEXT,
        media_urls TEXT,
        urls TEXT,
        hashtags TEXT,
        user_mentions TEXT,
        source TEXT,
        FOREIGN KEY (author_id) REFERENCES authors(id)
    )
    """)

    cursor.execute(
        f"""
            create virtual table if not exists {EMBEDDINGS_TABLE} using vec0(
                sample_embedding float[{EMBEDDINGS_LEN}] distance_metric=cosine,
                tweet_text text,
                tweet_id text,
            );
        """
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smart_list_summaries (
        list_id INTEGER NOT NULL,
        filters_hash TEXT NOT NULL,
        summary TEXT NOT NULL,
        status TEXT DEFAULT 'completed',
        model TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (list_id, filters_hash)
    )
    """)

    # Handle migration for existing databases that don't have the model column
    try:
        cursor.execute("SELECT model FROM smart_list_summaries LIMIT 1")
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        cursor.execute("ALTER TABLE smart_list_summaries ADD COLUMN model TEXT")
        print("Added model column to smart_list_summaries table")

    conn.commit()


# def upsert_author(conn, author_data):
#     cursor = conn.cursor()
#     cursor.execute(
#         """
#     INSERT OR REPLACE INTO authors (id, username, screen_name, name, description, avatar_url, banner_url, followers_count, following_count, statuses_count, verified, blue_verified, location, created_at)
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """,
#         author_data,
#     )
#     conn.commit()


# def upsert_tweet(conn, tweet_data):
#     cursor = conn.cursor()
#     cursor.execute(
#         """
#     INSERT OR REPLACE INTO tweets (id, author_id, text, created_at, conversation_id, in_reply_to_user_id, in_reply_to_status_id, lang, retweet_count, favorite_count, reply_count, quote_count, bookmark_count, view_count, is_quote_status, possibly_sensitive, retweeted, favorited, bookmarked, note_tweet_text, media_urls, urls, hashtags, user_mentions, source)
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """,
#         tweet_data,
#     )
#     conn.commit()


# def get_tweets_without_embeddings(conn, limit=10):
#     """Get tweets that don't have embeddings yet"""
#     cursor = conn.cursor()
#     cursor.execute(
#         f"""
#     SELECT tweets.*
#     FROM tweets
#     LEFT JOIN {EMBEDDINGS_TABLE} ON tweets.id = {EMBEDDINGS_TABLE}.tweet_id
#     WHERE {EMBEDDINGS_TABLE}.tweet_id IS NULL
#     LIMIT ?
#     """,
#         (limit,),
#     )
#     return cursor.fetchall()


# def upsert_tweet_embeddings(conn, embeddings_data):
#     """Insert or update tweet embeddings"""
#     cursor = conn.cursor()
#     cursor.executemany(
#         f"""
#     INSERT OR REPLACE INTO {EMBEDDINGS_TABLE} (tweet_id, sample_embedding, tweet_text)
#     VALUES (?, ?, ?)
#     """,
#         [
#             (
#                 data["tweet_id"],
#                 serialize_float32(data["embedding"]),
#                 data["tweet_text"],
#             )
#             for data in embeddings_data
#         ],
#     )
#     conn.commit()


# def search_tweets_by_vector(
#     conn, query_embedding: list[float], similarity_threshold=0.4, limit=50
# ):
#     """Search tweets by vector similarity with a similarity threshold"""
#     cursor = conn.cursor()
#     # Convert similarity threshold to cosine distance threshold
#     # similarity_threshold of 0.8 means we want cosine distance <= 0.2 (1.0 - 0.8)
#     cosine_distance_threshold = 1.0 - similarity_threshold

#     cursor.execute(
#         f"""
#     SELECT tweets.*, embeddings.distance, authors.screen_name, authors.name as author_name
#     FROM (
#         SELECT tweet_id, tweet_text, distance
#         FROM {EMBEDDINGS_TABLE}
#         WHERE sample_embedding MATCH ?
#         ORDER BY distance
#         LIMIT ?
#     ) as embeddings
#     JOIN tweets ON embeddings.tweet_id = tweets.id
#     JOIN authors ON tweets.author_id = authors.id
#     WHERE embeddings.distance <= ?
#     ORDER BY embeddings.distance
#     """,
#         (serialize_float32(query_embedding), limit, cosine_distance_threshold),
#     )
#     return cursor.fetchall()


# def get_tweets_by_authors_and_timeframe(
#     conn,
#     author_screen_names: list[str],
#     start_date: datetime,
#     end_date: datetime = None,
#     query_embedding: list[float] = None,
#     similarity_threshold: float = 0.4,
#     limit: int = 50,
# ):
#     """Get tweets from specific authors within a timeframe, optionally filtered by vector similarity"""
#     if end_date is None:
#         end_date = datetime.now()

#     cursor = conn.cursor()

#     if query_embedding:
#         # Use vector search with author and time filtering
#         # Convert similarity threshold to cosine distance threshold
#         cosine_distance_threshold = 1.0 - similarity_threshold
#         placeholders = ",".join(["?"] * len(author_screen_names))
#         cursor.execute(
#             f"""
#         SELECT tweets.*, embeddings.distance, authors.screen_name, authors.name as author_name, authors.avatar_url
#         FROM (
#             SELECT tweet_id, tweet_text, distance
#             FROM {EMBEDDINGS_TABLE}
#             WHERE sample_embedding MATCH ?
#             ORDER BY distance
#             LIMIT ?
#         ) as embeddings
#         JOIN tweets ON embeddings.tweet_id = tweets.id
#         JOIN authors ON tweets.author_id = authors.id
#         WHERE authors.screen_name IN ({placeholders})
#         AND tweets.created_at >= ?
#         AND tweets.created_at <= ?
#         AND embeddings.distance <= ?
#         ORDER BY embeddings.distance
#         """,
#             (
#                 serialize_float32(query_embedding),
#                 limit * 2,  # Get more results initially to filter properly
#                 *author_screen_names,
#                 start_date.isoformat(),
#                 end_date.isoformat(),
#                 cosine_distance_threshold,
#             ),
#         )
#     else:
#         # Regular search without vector similarity
#         placeholders = ",".join(["?"] * len(author_screen_names))
#         cursor.execute(
#             f"""
#         SELECT tweets.*, authors.screen_name, authors.name as author_name, authors.avatar_url
#         FROM tweets
#         JOIN authors ON tweets.author_id = authors.id
#         WHERE authors.screen_name IN ({placeholders})
#         AND tweets.created_at >= ?
#         AND tweets.created_at <= ?
#         ORDER BY tweets.created_at DESC
#         LIMIT ?
#         """,
#             (*author_screen_names, start_date.isoformat(), end_date.isoformat(), limit),
#         )

#     return cursor.fetchall()


# def get_tweet_count(conn):
#     cursor = conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM tweets")
#     return cursor.fetchone()[0]


# def get_author_count(conn):
#     cursor = conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM authors")
#     return cursor.fetchone()[0]


def get_cached_summary(conn, list_id, filters_hash):
    """Get cached summary if available"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT summary, status, model FROM smart_list_summaries WHERE list_id = ? AND filters_hash = ?",
        (list_id, filters_hash),
    )
    result = cursor.fetchone()
    return result if result else None


def upsert_summary(
    conn, list_id, filters_hash, summary, status="completed", model=None
):
    """Insert or update cached summary"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT OR REPLACE INTO smart_list_summaries
        (list_id, filters_hash, summary, status, model, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (list_id, filters_hash, summary, status, model, now, now),
    )
    conn.commit()
