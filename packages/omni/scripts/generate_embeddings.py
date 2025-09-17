#!/usr/bin/env python3
"""
Script to generate embeddings for tweets using Ollama's embedding model.
Uses gemma:2b embedding model with 768-dimensional vectors.
"""

import json
import sys
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent))

from omni.db import (
    get_tweets_without_embeddings,
    get_twitter_connection,
    upsert_tweet_embeddings,
)


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
        print(f"Error getting embedding for text: {str(e)[:100]}...")
        return None


def prepare_tweet_text(tweet_row):
    """Prepare tweet text for embedding by combining relevant fields"""
    text_parts = []

    # Main tweet text
    if tweet_row["text"]:
        text_parts.append(tweet_row["text"])

    # Note tweet text (if available, usually longer form)
    if tweet_row["note_tweet_text"]:
        text_parts.append(tweet_row["note_tweet_text"])

    # Parse and add hashtags
    try:
        hashtags = json.loads(tweet_row["hashtags"]) if tweet_row["hashtags"] else []
        if hashtags:
            text_parts.append(" ".join(f"#{tag}" for tag in hashtags))
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse and add URLs (display URLs for context)
    try:
        urls = json.loads(tweet_row["urls"]) if tweet_row["urls"] else []
        if urls:
            display_urls = [
                url.get("display_url", "") for url in urls if url.get("display_url")
            ]
            if display_urls:
                text_parts.append(" ".join(display_urls))
    except (json.JSONDecodeError, TypeError):
        pass

    return " ".join(text_parts).strip()


def main():
    print("Generating embeddings for tweets using Ollama nomic-embed-text model...")

    # Test Ollama connection first
    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        test_response.raise_for_status()
        print("✓ Ollama is running")
    except Exception as e:
        print(f"✗ Error connecting to Ollama: {e}")
        print("Make sure Ollama is running with: ollama serve")
        print(
            "And that you have the nomic-embed-text model: ollama pull nomic-embed-text"
        )
        return

    batch_size = 100  # Process embeddings in batches

    with get_twitter_connection() as conn:
        while True:
            # Get tweets without embeddings
            tweets_without_embeddings = get_tweets_without_embeddings(
                conn, limit=batch_size
            )

            if not tweets_without_embeddings:
                print("✓ All tweets have embeddings!")
                break

            print(f"Processing {len(tweets_without_embeddings)} tweets...")

            embeddings_batch = []

            # Generate embeddings with progress bar
            for tweet_row in tqdm(
                tweets_without_embeddings, desc="Generating embeddings"
            ):
                tweet_text = prepare_tweet_text(tweet_row)

                if not tweet_text.strip():
                    print(f"Skipping tweet {tweet_row['id']} - no text content")
                    continue

                # Get embedding
                embedding = get_ollama_embedding(tweet_text)

                if embedding is None:
                    print(f"Failed to get embedding for tweet {tweet_row['id']}")
                    continue

                if len(embedding) != 768:
                    print(
                        f"Warning: Expected 768-dim embedding but got {len(embedding)} for tweet {tweet_row['id']}"
                    )

                embeddings_batch.append(
                    {
                        "tweet_id": tweet_row["id"],
                        "embedding": embedding,
                        "tweet_text": tweet_text[
                            :1000
                        ],  # Store first 1000 chars for reference
                    }
                )

            # Insert embeddings in batch
            if embeddings_batch:
                print(f"Inserting {len(embeddings_batch)} embeddings into database...")
                try:
                    upsert_tweet_embeddings(conn, embeddings_batch)
                    print(f"✓ Inserted {len(embeddings_batch)} embeddings")
                except Exception as e:
                    print(f"✗ Error inserting embeddings: {e}")

            # If we processed less than the batch size, we're done
            if len(tweets_without_embeddings) < batch_size:
                break

    print("✓ Embedding generation complete!")


if __name__ == "__main__":
    main()
