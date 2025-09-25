import hashlib
import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from omni.db import get_omni_connection
from omni.settings import settings
from omni.vectorstore_queries import (
    search_tweets,
)

CLAUDE_MODEL = "claude-opus-4-1-20250805"


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
            model=CLAUDE_MODEL,
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


def generate_summary(query_text, tweets_text):
    """Generate a summary from tweets text using Ollama or Anthropic"""
    if not tweets_text.strip():
        return "No tweets available for summary.", None

    prompt = f"""
Please analyze the following tweets and create a concise bullet-point summary highlighting the key themes in these sources.
Only include sources in the summary if they are relevant to the query: {query_text}, if its not relevant, don't include it.
For each theme, include the source that it came from formatted as [@handle]
Do not create more than 6 main themes, only create a theme if multiple sources talk about the same theme.
Format as bullet points with brief(!) descriptions:

Tweets:
{tweets_text}

Summary (use bullet points starting with •):
remember to double check if each theme has multiple sources, otherwise exclude it."""

    use_anthropic = settings.use_anthropic

    if use_anthropic:
        print("Using Anthropic")
        summary = get_anthropic_completion(prompt)
        if summary:
            return summary, CLAUDE_MODEL
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


def get_intended_model():
    """Get the model that will be used for summary generation"""

    if settings.use_anthropic:
        return "claude-3-haiku-20240307"
    return "llama3.2:1b"


def generate_filters_hash(list_source):
    """Generate a hash for the list source filters for caching"""
    # Convert Pydantic model to dict if necessary
    if hasattr(list_source, "model_dump"):
        list_source_dict = list_source.model_dump()
    elif hasattr(list_source, "dict"):
        list_source_dict = list_source.dict()
    else:
        list_source_dict = list_source

    filters_str = json.dumps(list_source_dict, sort_keys=True)
    return hashlib.md5(filters_str.encode()).hexdigest()


def generate_summary_async(list_id, list_source, filters_hash):
    """Generate summary in background thread"""
    try:
        # Mark as generating
        upsert_summary(list_id, filters_hash, "", "generating")

        # Generate the actual summary
        summary, model = _generate_smart_list_summary_internal(list_source)

        # Save completed summary
        if model is not None:
            upsert_summary(list_id, filters_hash, summary, "completed", model)

    except Exception as e:
        print(f"Error in async summary generation: {e}")
        upsert_summary(list_id, filters_hash, "Error generating summary", "error")


def _generate_smart_list_summary_internal(list_source):
    """Internal function to generate summary (used by both sync and async)"""

    # Convert Pydantic model to dict if necessary
    if hasattr(list_source, "model_dump"):
        list_source_dict = list_source.model_dump()
    elif hasattr(list_source, "dict"):
        list_source_dict = list_source.dict()
    else:
        list_source_dict = list_source

    filters = list_source_dict["filters"]
    authors = [
        author.lstrip("@") for author in filters.get("authors", [])
    ]  # Remove @ prefix

    if not authors:
        return "No authors specified for summary.", None

    # Parse date range
    start_date = datetime.fromisoformat(filters["dateRange"]["from"])
    end_date = datetime.fromisoformat(filters["dateRange"]["to"])

    # Get RAG query text (only if query is provided and not empty)
    query_text = None
    if filters.get("ragQuery") and filters["ragQuery"].strip():
        query_text = filters["ragQuery"]

    try:
        tweet_items = search_tweets(
            query_text=query_text,
            author_screen_names=authors,
            start_date=start_date,
            end_date=end_date,
            similarity_threshold=filters.get("threshold", 0.4) if query_text else 0.0,
            limit=50,
        )

        if not tweet_items:
            return "No tweets found matching the criteria.", None

        # Combine tweet texts for summary
        tweets_text = "\n\n".join(
            [
                f"{tweet_item.author['handle']}: {tweet_item.content}"
                for tweet_item in tweet_items[:20]  # Limit to first 20 for summary
                if tweet_item.content
            ]
        )

        return generate_summary(query_text, tweets_text)

    except Exception as e:
        print(f"Error generating smart list summary: {e}")
        return "Unable to generate summary due to an error.", None


def get_or_generate_smart_list_summary(list_id, list_source):
    """Get cached summary or generate new one (async if needed)"""

    filters_hash = generate_filters_hash(list_source)

    cached = get_cached_summary(list_id, filters_hash)

    if cached:
        print("Getting cached summary")
        summary, status, model = cached

        # If we have a cached result but no model info, update it with intended model for generating status
        if status == "generating" and model is None:
            intended_model = get_intended_model()
            return {"summary": summary, "status": status, "model": intended_model}

        return {"summary": summary, "status": status, "model": model}
    else:
        print("Geneting new summary")

        # No cached summary, start async generation
        intended_model = get_intended_model()
        thread = threading.Thread(
            target=generate_summary_async, args=(list_id, list_source, filters_hash)
        )
        thread.daemon = True
        thread.start()

        return {"summary": "", "status": "generating", "model": intended_model}


# Summary cache management (using the same SQLite tables for now)
def get_cached_summary(list_id: int, filters_hash: str) -> Optional[tuple]:
    """Get cached summary if available"""

    try:
        with get_omni_connection() as conn:
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

    try:
        with get_omni_connection() as conn:
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

    try:
        with get_omni_connection() as conn:
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
