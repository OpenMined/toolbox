"""
ToolboxStore-based implementations of tweet query functions.
These replace the old SQLite-based implementations in db.py.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

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
        documents = (
            store.search_documents()
            .where({"author.screen_name__in": author_screen_names})
            .where({"created_at__gte": start_date})
            .where({"created_at__lt": end_date})
            .get()
        )
        print("INITIAL DOCUMENTS", len(documents))
        if query_text and query_text.strip():
            res_documents = (
                store.search_chunks()
                .where({"id__in": [doc.id for doc in documents]})
                .semantic(query_text)
                .chunk_limit(limit * 10)
                .rerank()
                .get_documents()
            )
            documents = []
            for doc in res_documents:
                max_doc_score = max(chunk.score for chunk in doc.chunks)
                if max_doc_score >= similarity_threshold:
                    documents.append(doc)
            print("got documents", len(documents))

        converted_documents = [convert_tweet_to_item(doc) for doc in documents]

        return converted_documents

        # chunks_query = store.search_chunks()
        # if query_text.strip():
        #     chunks_query = chunks_query.semantic(query_text)
        # documents = chunks_query.chunk_limit(limit * 10).get_doc()

        # if query_text and query_text.strip():
        #     # Use semantic search with text query

        #     # Get documents for chunks that pass similarity threshold
        #     tweet_ids = []
        #     chunk_similarities = {}

        #     for chunk in chunks:
        #         similarity = 1.0 - chunk.distance
        #         if similarity >= similarity_threshold:
        #             tweet_ids.append(chunk.document_id)
        #             chunk_similarities[chunk.document_id] = similarity

        #     if not tweet_ids:
        #         return []

        #     # Get documents by IDs from vector search
        #     docs = []
        #     for tweet_id in tweet_ids:
        #         doc_results = store.search_documents().where({"id": tweet_id}).get()
        #         if doc_results:
        #             docs.extend(doc_results)

        #     # Apply filters and convert to TweetItems
        #     results = []
        #     for tweet in docs:
        #         # Apply author filtering
        #         if author_screen_names:
        #             tweet_author = (
        #                 tweet.author.get("screen_name", "") if tweet.author else ""
        #             )
        #             if tweet_author not in author_screen_names:
        #                 continue

        #         # Apply date filtering
        #         if not passes_date_filter(tweet):
        #             continue

        #         # Convert to TweetItem with similarity score
        #         similarity_score = chunk_similarities.get(tweet.id)
        #         if similarity_score is not None:
        #             tweet_item = convert_tweet_to_item(
        #                 tweet, round(similarity_score, 3)
        #             )
        #             results.append(tweet_item)

        #         if len(results) >= limit:
        #             break

        #     return results

        # else:
        #     # Regular search without vector similarity
        #     docs = store.search_documents().limit(limit * 2).get()

        #     # Apply filters and convert to TweetItems
        #     results = []
        #     for tweet in docs:
        #         # Apply author filtering
        #         if author_screen_names:
        #             tweet_author = (
        #                 tweet.author.get("screen_name", "") if tweet.author else ""
        #             )
        #             if tweet_author not in author_screen_names:
        #                 continue

        #         # Apply date filtering
        #         if not passes_date_filter(tweet):
        #             continue

        #         # Convert to TweetItem
        #         tweet_item = convert_tweet_to_item(tweet, None)
        #         results.append(tweet_item)

        #         if len(results) >= limit:
        #             break

        #     # Sort by created_at descending
        #     results.sort(key=lambda x: x.timestamp, reverse=True)
        #     return results[:limit]

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


# Summary cache management (using the same SQLite tables for now)
def get_cached_summary(list_id: int, filters_hash: str) -> Optional[tuple]:
    """Get cached summary if available"""
    from omni.db import get_twitter_connection

    try:
        with get_twitter_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT summary, status, model FROM smart_list_summaries WHERE list_id = ? AND filters_hash = ?",
                (list_id, filters_hash),
            )
            result = cursor.fetchone()
            return result if result else None
    except Exception as e:
        print(f"Error getting cached summary: {e}")
        return None


def upsert_summary(
    list_id: int,
    filters_hash: str,
    summary: str,
    status: str = "completed",
    model: Optional[str] = None,
):
    """Insert or update cached summary"""
    from omni.db import get_twitter_connection

    try:
        with get_twitter_connection() as conn:
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
    except Exception as e:
        print(f"Error upserting summary: {e}")


def clear_summary_cache(list_id: int, filters_hash: str) -> Dict[str, Any]:
    """Clear cached summary for a specific list and filter combination"""
    from omni.db import get_twitter_connection

    try:
        with get_twitter_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM smart_list_summaries WHERE list_id = ? AND filters_hash = ?",
                (list_id, filters_hash),
            )
            conn.commit()
            deleted = cursor.rowcount
            return {
                "message": f"Cleared cache for list {list_id}",
                "deleted_rows": deleted,
            }
    except Exception as e:
        return {"message": f"Error clearing cache: {str(e)}"}
