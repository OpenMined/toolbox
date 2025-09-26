import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import numpy as np
import sqlite_vec
from toolbox_store import ToolboxStore
from toolbox_store.models import StoreConfig

from .models import SmartListAPIResult, SmartListCreate, SmartListDB
from .vectorstore_models import Tweet

HOME = Path.home()
OMNI_DB_PATH = HOME / ".twitter-mcp" / "db.sqlite"
TWITTER_VECTORSTORE_DB_PATH = HOME / ".twitter-mcp" / "tweet_toolbox_store.db"
OMNI_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

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


def _get_omni_connection(path: Path = OMNI_DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    create_tables(conn)
    return conn


@contextmanager
def get_omni_connection(path: Path = OMNI_DB_PATH):
    conn = _get_omni_connection(path)
    try:
        yield conn
    finally:
        conn.close()


def create_tables(conn):
    cursor = conn.cursor()

    # Smart lists main table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smart_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        item_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        user_email TEXT NOT NULL
    )
    """)

    # List sources - each smart list can have multiple data sources
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS list_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        data_source_id TEXT NOT NULL,
        FOREIGN KEY (list_id) REFERENCES smart_lists (id) ON DELETE CASCADE
    )
    """)

    # List filters - filters for each list source
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS list_filters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_source_id INTEGER NOT NULL,
        date_range_from TEXT,
        date_range_to TEXT,
        rag_query TEXT,
        threshold REAL DEFAULT 0.6,
        FOREIGN KEY (list_source_id) REFERENCES list_sources (id) ON DELETE CASCADE
    )
    """)

    # Authors for each list source
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasource_authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_source_id INTEGER NOT NULL,
        author TEXT NOT NULL,
        FOREIGN KEY (list_source_id) REFERENCES list_sources (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smart_list_summaries (
        list_id INTEGER NOT NULL,
        filters_hash TEXT NOT NULL,
        summary TEXT NOT NULL,
        status TEXT DEFAULT 'completed',
        model TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (list_id, filters_hash),
        FOREIGN KEY (list_id) REFERENCES smart_lists (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS followed_lists (
        user_email TEXT NOT NULL,
        list_id INTEGER NOT NULL,
        PRIMARY KEY (user_email, list_id),
        FOREIGN KEY (list_id) REFERENCES smart_lists (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Run database migrations
    from .migrations.v1 import run_v1_migrations

    run_v1_migrations(conn)


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


# def get_cached_summary(conn, list_id, filters_hash):
#     """Get cached summary if available"""
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT summary, status, model FROM smart_list_summaries WHERE list_id = ? AND filters_hash = ?",
#         (list_id, filters_hash),
#     )
#     result = cursor.fetchone()
#     return result if result else None


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


def follow_list(conn, user_email: str, list_id: int):
    """Follow a smart list for a user"""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO followed_lists (user_email, list_id)
        VALUES (?, ?)
        """,
        (user_email, list_id),
    )
    conn.commit()


def unfollow_list(conn, user_email: str, list_id: int):
    """Unfollow a smart list for a user"""
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM followed_lists
        WHERE user_email = ? AND list_id = ?
        """,
        (user_email, list_id),
    )
    conn.commit()


def get_followed_list_ids(conn, user_email: str):
    """Get list of followed list IDs for a user"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT list_id FROM followed_lists WHERE user_email = ?",
        (user_email,),
    )
    return [row[0] for row in cursor.fetchall()]


def is_list_followed(conn, user_email: str, list_id: int):
    """Check if a user is following a specific list"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM followed_lists WHERE user_email = ? AND list_id = ?",
        (user_email, list_id),
    )
    return cursor.fetchone() is not None


def create_user(conn, email: str):
    """Create a new user or return existing user"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (email, created_at)
        VALUES (?, ?)
        """,
        (email, now),
    )
    conn.commit()

    # Return the user
    cursor.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


def get_user_by_email(conn, email: str):
    """Get user by email"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


def initialize_dev_user():
    """Initialize the dev@example.com user for development"""
    with get_omni_connection() as conn:
        return create_user(conn, "dev@example.com")


def insert_smart_list(conn, name: str, user_email: str, item_count: int = 0):
    """Insert a new smart list and return its ID"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO smart_lists (name, item_count, created_at, user_email)
        VALUES (?, ?, ?, ?)
    """,
        (name, item_count, now, user_email),
    )

    list_id = cursor.lastrowid
    conn.commit()
    return list_id


def insert_list_source(conn, list_id: int, data_source_id: str):
    """Insert a list source and return its ID"""
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO list_sources (list_id, data_source_id)
        VALUES (?, ?)
    """,
        (list_id, data_source_id),
    )

    source_id = cursor.lastrowid
    conn.commit()
    return source_id


def insert_list_filters(
    conn,
    list_source_id: int,
    date_range_from: str = None,
    date_range_to: str = None,
    rag_query: str = None,
    threshold: float = 0.6,
):
    """Insert filters for a list source"""
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO list_filters (list_source_id, date_range_from, date_range_to, rag_query, threshold)
        VALUES (?, ?, ?, ?, ?)
    """,
        (list_source_id, date_range_from, date_range_to, rag_query, threshold),
    )

    conn.commit()


def insert_datasource_author(conn, list_source_id: int, author: str):
    """Insert an author for a list source"""
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO datasource_authors (list_source_id, author)
        VALUES (?, ?)
    """,
        (list_source_id, author),
    )

    conn.commit()


def get_smart_list_api_result_by_id(conn, list_id: int) -> SmartListAPIResult:
    """Get a smart list by its ID"""
    smart_lists = get_all_smart_lists_api_result(conn)
    return next((sl for sl in smart_lists if sl.id == list_id), None)


def _get_smart_lists_api_result(
    conn, only_for_user: str = None, exclude_user: str = None, current_user: str = None
) -> list["SmartListAPIResult"]:
    """Common function to get smart lists with filtering and following status"""
    cursor = conn.cursor()

    base_query = """
        SELECT
            sl.id, sl.name, sl.item_count, sl.created_at, sl.user_email,
            ls.id as source_id, ls.data_source_id,
            lf.date_range_from, lf.date_range_to, lf.rag_query, lf.threshold,
            da.author
        FROM smart_lists sl
        LEFT JOIN list_sources ls ON sl.id = ls.list_id
        LEFT JOIN list_filters lf ON ls.id = lf.list_source_id
        LEFT JOIN datasource_authors da ON ls.id = da.list_source_id
    """

    params = []
    where_conditions = []

    if only_for_user:
        where_conditions.append("sl.user_email = ?")
        params.append(only_for_user)

    if exclude_user:
        where_conditions.append("sl.user_email != ?")
        params.append(exclude_user)

    if where_conditions:
        query = f"{base_query} WHERE {' AND '.join(where_conditions)} ORDER BY sl.id, ls.id, da.id"
    else:
        query = f"{base_query} ORDER BY sl.id, ls.id, da.id"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Get followed list IDs if current_user is provided
    followed_ids = []
    if current_user:
        followed_ids = get_followed_list_ids(conn, current_user)

    # Group results by smart list
    lists_data = {}
    for row in rows:
        list_id = row["id"]
        if list_id not in lists_data:
            smart_list = SmartListDB.from_sql_row(row)
            lists_data[list_id] = {"smart_list": smart_list, "sources_data": []}

        if row["source_id"]:
            lists_data[list_id]["sources_data"].append(row)

    # Convert to SmartListAPIResult models
    result = []
    for data in lists_data.values():
        following = data["smart_list"].id in followed_ids if current_user else False
        api_result = SmartListAPIResult.from_db_data(
            data["smart_list"], data["sources_data"], following=following
        )
        result.append(api_result)

    return result


def get_all_smart_lists_api_result(conn) -> list["SmartListAPIResult"]:
    """Get all smart lists with their sources, filters, and authors using a single query"""
    return _get_smart_lists_api_result(conn)


def get_my_lists_api_result(conn, user_email: str) -> list["SmartListAPIResult"]:
    """Get smart lists created by the user, with following status"""
    return _get_smart_lists_api_result(
        conn, only_for_user=user_email, current_user=user_email
    )


def get_community_lists_api_result(conn, user_email: str) -> list["SmartListAPIResult"]:
    """Get smart lists NOT created by the user (community lists), with following status"""
    return _get_smart_lists_api_result(
        conn, exclude_user=user_email, current_user=user_email
    )


def delete_smart_list(conn, list_id: int, user_email: str) -> bool:
    """Delete a smart list if owned by the user. Returns True if deleted, False otherwise."""
    cursor = conn.cursor()

    # Check if the user owns this list
    cursor.execute("SELECT user_email FROM smart_lists WHERE id = ?", (list_id,))
    row = cursor.fetchone()

    if not row or row["user_email"] != user_email:
        return False  # User doesn't own this list or list doesn't exist

    # Delete the list (CASCADE will handle related tables)
    cursor.execute("DELETE FROM smart_lists WHERE id = ?", (list_id,))
    conn.commit()

    return cursor.rowcount > 0


def create_smart_list_from_request(
    conn, list_data: SmartListCreate, user_email: str
) -> int:
    """Create a smart list from SmartListCreate request and auto-follow it. Returns the list ID."""

    # Insert the smart list
    list_id = insert_smart_list(conn, list_data.name, user_email, 0)

    # Insert sources and their filters/authors
    for list_source in list_data.listSources:
        source_id = insert_list_source(conn, list_id, list_source.dataSourceId)

        filters = list_source.filters
        insert_list_filters(
            conn,
            source_id,
            filters.dateRange.get("from"),
            filters.dateRange.get("to"),
            filters.ragQuery,
            filters.threshold,
        )

        # Insert authors
        for author in filters.authors:
            insert_datasource_author(conn, source_id, author)

    # Auto-follow the created list
    follow_list(conn, user_email, list_id)

    return list_id


def initialize_mock_smart_lists():
    """Insert mock smart lists data into the database"""
    from .mock_data import get_mock_smart_lists

    with get_omni_connection() as conn:
        # Check if we already have smart lists
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM smart_lists")
        count = cursor.fetchone()[0]

        if count > 0:
            return  # Already initialized

        mock_lists = get_mock_smart_lists()

        for mock_list in mock_lists:
            # Insert the smart list
            list_id = insert_smart_list(
                conn, mock_list["name"], "example@list.org", mock_list["itemCount"]
            )

            # Insert sources and their filters/authors
            for list_source in mock_list["listSources"]:
                source_id = insert_list_source(
                    conn, list_id, list_source["dataSourceId"]
                )

                filters = list_source["filters"]
                insert_list_filters(
                    conn,
                    source_id,
                    filters["dateRange"].get("from"),
                    filters["dateRange"].get("to"),
                    filters.get("ragQuery"),
                    filters.get("threshold", 0.6),
                )

                # Insert authors if they exist
                if "authors" in filters:
                    for author in filters["authors"]:
                        insert_datasource_author(conn, source_id, author)
