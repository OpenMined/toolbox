from datetime import datetime

from omni.vectorstore_queries import (
    search_tweets,
)


def query_twitter_data(list_source):
    """Query Twitter data based on list source filters"""

    filters = list_source.filters
    authors = (
        [author.lstrip("@") for author in filters.authors] if filters.authors else None
    )  # Remove @ prefix

    # Parse date range
    from_date = filters.dateRange["from"]
    to_date = filters.dateRange["to"]
    if from_date:
        start_date = datetime.fromisoformat(from_date + "T00:00:00Z")
    else:
        start_date = None
    if to_date:
        end_date = datetime.fromisoformat(to_date + "T23:59:59Z")
    else:
        end_date = None

    # Get RAG query text (only if query is provided and not empty)
    query_text = None
    if filters.ragQuery and filters.ragQuery.strip():
        query_text = filters.ragQuery

    # If no authors and no RAG query, return empty (nothing to search for)
    if not authors and not query_text:
        return []

    try:
        # Use the unified search function
        tweet_items = search_tweets(
            query_text=query_text,
            author_screen_names=authors,
            start_date=start_date,
            end_date=end_date,
            similarity_threshold=filters.threshold,
            limit=20,  # Limit to 20 for display
        )

        # Convert TweetItem objects to dictionaries for API response
        return [tweet_item.model_dump() for tweet_item in tweet_items]

    except Exception:
        import traceback

        traceback.print_exc()
        # print(f"Error querying Twitter data: {e}")
        return []
