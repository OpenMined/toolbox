import hashlib
import json
import os
import threading
from datetime import datetime

import requests

from omni.db import (
    get_cached_summary,
    get_tweets_by_authors_and_timeframe,
    get_twitter_connection,
    search_tweets_by_vector,
    upsert_summary,
)
from omni.settings import settings

TWITTER_DB_AVAILABLE = True


def get_ollama_completion(prompt, model="llama3.2:1b"):
    """Get completion from Ollama API"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 500,  # Limit response length
                },
            },
            timeout=60,  # Reduced timeout
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("response", "").strip()
        return result
    except Exception as e:
        print(f"Error getting Ollama completion: {e}")
        return None


def get_anthropic_completion(prompt):
    """Get completion from Anthropic API"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment")
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except ImportError:
        print("Anthropic package not installed")
        return None
    except Exception as e:
        print(f"Error getting Anthropic completion: {e}")
        return None


def generate_summary(tweets_text):
    """Generate a summary from tweets text using Ollama or Anthropic"""
    if not tweets_text.strip():
        return "No tweets available for summary.", None

    prompt = f"""Please analyze the following tweets and create a concise bullet-point summary highlighting the key themes, insights, and trends. Format as bullet points with brief descriptions:

Tweets:
{tweets_text}

Summary (use bullet points starting with •):"""

    use_anthropic = settings.use_anthropic

    if use_anthropic:
        print("Using Anthropic")
        summary = get_anthropic_completion(prompt)
        if summary:
            return summary, "claude-3-haiku-20240307"
        print("Anthropic failed, falling back to Ollama")

    # Default to Ollama
    summary = get_ollama_completion(prompt)
    if summary:
        return summary, "llama3.2:1b"

    return "Unable to generate summary at this time.", None


def get_ollama_embedding(text, model="nomic-embed-text:latest"):
    """Get embedding from Ollama API"""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embedding")
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None


def query_twitter_data(list_source):
    """Query Twitter data based on list source filters"""
    if not TWITTER_DB_AVAILABLE:
        return []

    filters = list_source["filters"]
    authors = [
        author.lstrip("@") for author in filters.get("authors", [])
    ]  # Remove @ prefix

    # Parse date range
    start_date = datetime.fromisoformat(filters["dateRange"]["from"])
    end_date = datetime.fromisoformat(filters["dateRange"]["to"])

    # Get embedding for RAG query (only if query is provided and not empty)
    query_embedding = None
    if filters.get("ragQuery") and filters["ragQuery"].strip():
        query_embedding = get_ollama_embedding(filters["ragQuery"])
        if not query_embedding:
            print(f"Failed to get embedding for query: {filters['ragQuery']}")

    # If no authors and no RAG query, return empty (nothing to search for)
    if not authors and not query_embedding:
        return []

    try:
        with get_twitter_connection() as conn:
            if authors:
                # Search within specific authors
                tweets = get_tweets_by_authors_and_timeframe(
                    conn,
                    author_screen_names=authors,
                    start_date=start_date,
                    end_date=end_date,
                    query_embedding=query_embedding,
                    similarity_threshold=filters.get("threshold", 0.4)
                    if query_embedding
                    else 0.0,
                    limit=50,
                )
            elif query_embedding:
                # Search across all tweets using semantic search only
                tweets = search_tweets_by_vector(
                    conn,
                    query_embedding=query_embedding,
                    similarity_threshold=filters.get("threshold", 0.4),
                    limit=50,
                )
                # Filter by date range manually since search_tweets_by_vector doesn't do this
                tweets = [
                    tweet
                    for tweet in tweets
                    if start_date.isoformat()
                    <= tweet["created_at"]
                    <= end_date.isoformat()
                ]
            else:
                tweets = []

            # Convert to TweetItem format
            tweet_items = []
            for i, tweet in enumerate(tweets[:20]):  # Limit to first 20 for display
                # Calculate similarity score from distance (if available)
                similarity_score = None
                if "distance" in tweet.keys() and tweet["distance"] is not None:
                    # Convert distance to similarity (distance ranges from 0-2, similarity 0-1)
                    similarity_score = round(1.0 - tweet["distance"], 3)

                tweet_item = {
                    "id": str(tweet["id"])
                    if "id" in tweet.keys()
                    else f"mock_{i + 1}",  # Convert tweet ID to string to preserve precision
                    "type": "tweet",
                    "content": tweet["text"] if tweet["text"] else "",
                    "author": {
                        "name": tweet["author_name"]
                        if "author_name" in tweet.keys()
                        else "Unknown",
                        "handle": f"@{tweet['screen_name']}"
                        if "screen_name" in tweet.keys()
                        else "@unknown",
                        "avatarUrl": tweet["avatar_url"]
                        if "avatar_url" in tweet.keys() and tweet["avatar_url"]
                        else "https://via.placeholder.com/400x400?text=T",
                    },
                    "likes": tweet["favorite_count"]
                    if "favorite_count" in tweet.keys()
                    else 0,
                    "reactions": tweet["retweet_count"]
                    if "retweet_count" in tweet.keys()
                    else 0,
                    "timestamp": tweet["created_at"][:10]
                    if "created_at" in tweet.keys() and tweet["created_at"]
                    else "",
                    "similarity_score": similarity_score,
                }
                tweet_items.append(tweet_item)

            return tweet_items
    except Exception as e:
        print(f"Error querying Twitter data: {e}")
        return []


def get_intended_model():
    """Get the model that will be used for summary generation"""

    if settings.use_anthropic:
        return "claude-3-haiku-20240307"
    return "llama3.2:1b"


def generate_filters_hash(list_source):
    """Generate a hash for the list source filters for caching"""
    filters_str = json.dumps(list_source, sort_keys=True)
    return hashlib.md5(filters_str.encode()).hexdigest()


def generate_summary_async(list_id, list_source, filters_hash):
    """Generate summary in background thread"""
    try:
        # Mark as generating
        with get_twitter_connection() as conn:
            upsert_summary(conn, list_id, filters_hash, "", "generating")

        # Generate the actual summary
        summary, model = _generate_smart_list_summary_internal(list_source)

        # Save completed summary
        with get_twitter_connection() as conn:
            upsert_summary(conn, list_id, filters_hash, summary, "completed", model)

    except Exception as e:
        print(f"Error in async summary generation: {e}")
        with get_twitter_connection() as conn:
            upsert_summary(
                conn, list_id, filters_hash, "Error generating summary", "error"
            )


def _generate_smart_list_summary_internal(list_source):
    """Internal function to generate summary (used by both sync and async)"""
    if not TWITTER_DB_AVAILABLE:
        return "Database not available for summary generation.", None

    filters = list_source["filters"]
    authors = [
        author.lstrip("@") for author in filters.get("authors", [])
    ]  # Remove @ prefix

    if not authors:
        return "No authors specified for summary.", None

    # Parse date range
    start_date = datetime.fromisoformat(filters["dateRange"]["from"])
    end_date = datetime.fromisoformat(filters["dateRange"]["to"])

    # Get embedding for RAG query (only if query is provided and not empty)
    query_embedding = None
    if filters.get("ragQuery") and filters["ragQuery"].strip():
        query_embedding = get_ollama_embedding(filters["ragQuery"])

    try:
        with get_twitter_connection() as conn:
            tweets = get_tweets_by_authors_and_timeframe(
                conn,
                author_screen_names=authors,
                start_date=start_date,
                end_date=end_date,
                query_embedding=query_embedding,
                similarity_threshold=filters.get("threshold", 0.4)
                if query_embedding
                else 0.0,
                limit=50,
            )

            if not tweets:
                return "No tweets found matching the criteria.", None

            # Combine tweet texts for summary
            tweets_text = "\n\n".join(
                [
                    f"@{tweet['screen_name']}: {tweet['text']}"
                    for tweet in tweets[:20]  # Limit to first 20 for summary
                    if tweet["text"]
                ]
            )

            return generate_summary(tweets_text)

    except Exception as e:
        print(f"Error generating smart list summary: {e}")
        return "Unable to generate summary due to an error.", None


def get_or_generate_smart_list_summary(list_id, list_source):
    """Get cached summary or generate new one (async if needed)"""
    if not TWITTER_DB_AVAILABLE:
        return {
            "summary": "Database not available for summary generation.",
            "status": "error",
            "model": None,
        }

    filters_hash = generate_filters_hash(list_source)

    with get_twitter_connection() as conn:
        cached = get_cached_summary(conn, list_id, filters_hash)

        if cached:
            summary, status, model = cached

            # If we have a cached result but no model info, update it with intended model for generating status
            if status == "generating" and model is None:
                intended_model = get_intended_model()
                return {"summary": summary, "status": status, "model": intended_model}

            return {"summary": summary, "status": status, "model": model}

        # No cached summary, start async generation
        intended_model = get_intended_model()
        thread = threading.Thread(
            target=generate_summary_async, args=(list_id, list_source, filters_hash)
        )
        thread.daemon = True
        thread.start()

        return {"summary": "", "status": "generating", "model": intended_model}
