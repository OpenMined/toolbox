"""
ToolboxStore-based implementations of tweet query functions.
These replace the old SQLite-based implementations in db.py.
"""

from datetime import datetime
from typing import List, Optional

from omni.db import get_tweet_store
from omni.models import TweetItem


def search_tweets(
    query_text: Optional[str] = None,
    author_screen_names: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    similarity_threshold: float = 0.4,
    limit: int = 50,
) -> List[TweetItem]:
    """Unified tweet search function that returns TweetItem objects"""
    store = get_tweet_store()

    def convert_tweet_to_item(tweet, similarity_score=None):
        """Convert a Tweet document to TweetItem"""
        return TweetItem(
            id=str(tweet.tweet_id),
            type="tweet",
            content=tweet.content,
            author={
                "name": tweet.author.get("name", "Unknown")
                if tweet.author
                else "Unknown",
                "handle": f"@{tweet.author.get('screen_name', 'unknown')}"
                if tweet.author
                else "@unknown",
                "avatarUrl": tweet.author.get("avatar_url", "") if tweet.author else "",
            },
            likes=tweet.favorite_count,
            reactions=tweet.retweet_count,
            timestamp=tweet.created_at_tweet[:10] if tweet.created_at_tweet else "",
            similarity_score=similarity_score,
            tweet_type=tweet.tweet_type,
            interaction_context=tweet.interaction_context,
            media=tweet.media,  # Add media data from database
        )

    try:
        print(author_screen_names)
        print(start_date)
        print(end_date)
        print(similarity_threshold)
        print(limit)
        query = store.search_documents()
        if author_screen_names:
            query = query.where({"author.screen_name__in": author_screen_names})
        if start_date:
            query = query.where({"created_at__gte": start_date})
        if end_date:
            query = query.where({"created_at__lt": end_date})
        documents = query.get()
        print("INITIAL DOCUMENTS", len(documents))

        if query_text and query_text.strip():
            res_documents = (
                store.search_chunks()
                .where({"id__in": [doc.id for doc in documents]})
                .semantic(query_text)
                .chunk_limit(limit * 10)
                .get_documents()
            )
            documents = []
            similarities = []
            for doc in res_documents:
                similarity = 1 - min(chunk.distance for chunk in doc.chunks)
                if similarity >= similarity_threshold:
                    similarities.append(similarity)
                    documents.append(doc)
            print("got documents", len(documents))
        else:
            similarities = [None for _ in documents]

        converted_documents = [
            convert_tweet_to_item(doc, similarity)
            for doc, similarity in zip(documents, similarities)
        ]

        return converted_documents
    except Exception:
        import traceback

        traceback.print_exc()
        return []


def get_tweet_count() -> int:
    """Get total count of tweets in the store"""
    store = get_tweet_store()
    try:
        stats = store.db.stats()
        return stats.get("documents", 0)
    except Exception as e:
        print(f"Error getting tweet count: {e}")
        return 0


def get_author_count() -> int:
    """Get count of unique authors in the store"""
    store = get_tweet_store()
    try:
        # This is a bit tricky with ToolboxStore since authors are stored as JSON
        # We'll need to use the database directly for this
        cursor = store.db.conn.execute(
            f"SELECT COUNT(DISTINCT json_extract(author, '$.screen_name')) FROM {store.db.documents_table}"
        )
        return cursor.fetchone()[0] or 0
    except Exception as e:
        print(f"Error getting author count: {e}")
        return 0
