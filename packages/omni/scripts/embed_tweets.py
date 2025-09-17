#!/usr/bin/env python3
"""
Script to add embeddings to tweets using Ollama with two different models:
- gemma:2b (assuming this is what you meant by gemmaembed)
- nomic-embed-text:latest
"""

import json
import time
from pathlib import Path

import requests


def get_embedding_ollama(text, model):
    """Get embedding from Ollama API."""
    url = "http://localhost:11434/api/embeddings"

    payload = {"model": model, "prompt": text}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data.get("embedding", [])

    except requests.exceptions.RequestException as e:
        print(f"Error getting embedding for model {model}: {e}")
        return None


def main():
    """Main function to add embeddings to all tweets."""
    tweets_file = Path("./notebooks/combined_tweets.json")

    if not tweets_file.exists():
        print(f"Tweets file {tweets_file} not found!")
        return

    # Load tweets
    print("Loading tweets...")
    with open(tweets_file, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    print(f"Found {len(tweets)} tweets to process")

    # Models to use
    models = {"gemma": "embeddinggemma:latest", "nomic": "nomic-embed-text:latest"}

    # Process each tweet
    processed_count = 0
    total_tweets = len(tweets)

    for tweet_id, tweet_data in tweets.items():
        print(f"Processing tweet {processed_count + 1}/{total_tweets} (ID: {tweet_id})")

        content = tweet_data.get("content", "")
        if not content:
            print("  No content found, skipping...")
            processed_count += 1
            continue

        # Initialize or get existing embeddings dict
        embeddings = tweet_data.get("embeddings", {})

        # Get embeddings from both models (generate if missing)
        for model_name, model_id in models.items():
            if model_name not in embeddings:
                print(f"  Getting {model_name} embedding...")
                embedding = get_embedding_ollama(content, model_id)

                if embedding is not None:
                    embeddings[model_name] = embedding
                    print(f"    Got embedding of size {len(embedding)}")
                else:
                    print("    Failed to get embedding")

                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
            else:
                print(f"  {model_name} embedding already exists, skipping...")

        # Add embeddings to tweet data
        if embeddings:
            tweet_data["embeddings"] = embeddings

        processed_count += 1

        # Save progress every 50 tweets
        if processed_count % 50 == 0:
            print(f"  Saving progress ({processed_count}/{total_tweets})...")
            with open(tweets_file, "w", encoding="utf-8") as f:
                json.dump(tweets, f, indent=2, ensure_ascii=False)

    # Final save
    print("Saving final results...")
    with open(tweets_file, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)

    print(f"Completed processing {processed_count} tweets")

    # Summary
    tweets_with_embeddings = sum(1 for t in tweets.values() if "embeddings" in t)
    print(f"Total tweets with embeddings: {tweets_with_embeddings}")


if __name__ == "__main__":
    main()
