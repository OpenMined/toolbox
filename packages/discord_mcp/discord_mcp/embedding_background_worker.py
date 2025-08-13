import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests

from discord_mcp.db import (
    get_discord_connection,
    get_messages_without_embeddings,
    get_latest_message_timestamp,
    upsert_chunks,
)
from discord_mcp.settings import settings


def get_embedding_ollama(query: str) -> List[float]:
    """Get the embedding for a query using Ollama API"""
    import subprocess

    try:
        subprocess.run(
            ["ollama", "pull", "nomic-embed-text:v1.5"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    payload = {"model": "nomic-embed-text:v1.5", "prompt": query}
    response = requests.post(
        f"{settings.ollama_url}/api/embeddings", json=payload, timeout=10
    )
    response.raise_for_status()
    data = response.json()
    embedding = data.get("embedding")
    if embedding is None or not isinstance(embedding, list):
        raise ValueError(f"No embedding returned from Ollama: {data}")
    return embedding


def get_embedding_syftbox(query: str) -> List[float]:
    """Get embeddings from SyftBox (placeholder for now)"""
    raise NotImplementedError("SyftBox embedding provider not implemented yet")


def get_embedding(query: str) -> List[float]:
    """Get embedding based on configured provider"""
    if settings.embedding_provider == "ollama":
        return get_embedding_ollama(query)
    elif settings.embedding_provider == "syftbox":
        return get_embedding_syftbox(query)
    else:
        raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")


def check_rate_limit(conn) -> bool:
    """Check if we're within the rate limit for embeddings"""
    latest_timestamp = get_latest_message_timestamp(conn)
    if not latest_timestamp:
        return True

    # Parse the ISO timestamp and check if it's within the last hour
    try:
        latest_dt = datetime.fromisoformat(latest_timestamp.replace("Z", "+00:00"))
        one_hour_ago = datetime.now() - timedelta(hours=1)

        # Count messages from the last hour (simplified check)
        # In a real implementation, you might want to track actual embedding requests
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM messages 
            WHERE timestamp >= ?
        """,
            (one_hour_ago.isoformat(),),
        )

        recent_message_count = cursor.fetchone()[0]
        return recent_message_count < settings.max_messages_per_hour
    except Exception:
        return True


def chunk_messages(messages) -> List[Dict[str, Any]]:
    """Convert messages to chunks for embedding"""
    chunks = []
    for message in messages:
        if message.content.strip():  # Only process messages with content
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "message_ids": [message.id],
                "chunk_text": message.content,
            }
            chunks.append(chunk)
    return chunks


def run_embedding_background_worker_single(conn):
    """Run a single iteration of the embedding background worker"""
    print("Checking for messages without embeddings...")

    # Check rate limit
    if not check_rate_limit(conn):
        print(
            f"Rate limit reached ({settings.max_messages_per_hour} messages/hour), skipping this iteration"
        )
        return

    # Get messages that need embeddings
    messages = get_messages_without_embeddings(conn, limit=10)
    if not messages:
        print("No messages found without embeddings")
        return

    print(f"Found {len(messages)} messages to embed")

    # Chunk the messages
    chunks = chunk_messages(messages)
    if not chunks:
        print("No chunks created from messages")
        return

    # Generate embeddings for each chunk
    for chunk in chunks:
        try:
            print(f"Generating embedding for chunk {chunk['chunk_id'][:8]}...")
            embedding = get_embedding(chunk["chunk_text"])
            chunk["embedding"] = embedding
        except Exception as e:
            print(f"Failed to generate embedding for chunk {chunk['chunk_id']}: {e}")
            continue

    # Filter out chunks that failed to get embeddings
    successful_chunks = [c for c in chunks if "embedding" in c]

    if successful_chunks:
        print(f"Storing {len(successful_chunks)} chunks with embeddings...")
        upsert_chunks(conn, successful_chunks)
        print(f"Successfully stored {len(successful_chunks)} chunks")
    else:
        print("No chunks successfully embedded")


def run_embedding_background_worker_loop(stop_event: threading.Event = None):
    """Run the embedding background worker in a loop"""
    print("Starting embedding background worker loop...")

    while True:
        if stop_event and stop_event.is_set():
            break

        try:
            with get_discord_connection() as conn:
                run_embedding_background_worker_single(conn)
        except Exception as e:
            print(f"Error in embedding background worker: {e}")

        # Wait before next iteration
        time.sleep(30)  # 30 seconds between iterations

    print("Embedding background worker stopped")


def start_embedding_background_worker_embedding() -> threading.Thread:
    """Start the embedding background worker in a separate thread"""
    stop_event = threading.Event()
    thread = threading.Thread(
        target=run_embedding_background_worker_loop, args=(stop_event,), daemon=True
    )
    thread.stop_event = stop_event  # Attach stop_event to thread for external access
    thread.start()
    return thread
