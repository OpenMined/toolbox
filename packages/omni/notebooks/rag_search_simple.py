#!/usr/bin/env python3
"""
Simple script to search for tweets using cosine similarity with pure numpy.
No external dependencies except numpy.
"""

import json

import numpy as np
import requests


def cosine_similarity_numpy(a, b):
    """Calculate cosine similarity between two vectors using numpy."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def load_tweets(file_path):
    """Load tweets from JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
        print("Trying to load with error handling...")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            return json.loads(content)
        except Exception as e2:
            print(f"Still failed: {e2}")
            raise


def count_tweets_with_embeddings(tweets):
    """Count tweets that have both nomic and gemma embeddings."""
    nomic_count = 0
    gemma_count = 0
    both_count = 0

    for tweet_id, tweet_data in tweets.items():
        embeddings = tweet_data.get("embeddings", {})
        has_nomic = "nomic" in embeddings and embeddings["nomic"] is not None
        has_gemma = "gemma" in embeddings and embeddings["gemma"] is not None

        if has_nomic:
            nomic_count += 1
        if has_gemma:
            gemma_count += 1
        if has_nomic and has_gemma:
            both_count += 1

    return nomic_count, gemma_count, both_count


def create_query_vector(query_text, reference_vector):
    """
    Create a query vector based on simple text analysis.
    This is a simplified approach - in practice you'd use the same embedding model.
    """
    # Simple approach: create a vector that emphasizes certain dimensions
    # based on the query content
    query_vector = np.random.normal(0, 0.1, len(reference_vector))

    # Add some signal based on query characteristics
    query_lower = query_text.lower()

    # Boost certain dimensions based on query content
    if "rag" in query_lower:
        query_vector[:10] += 0.5  # Boost first 10 dimensions
    if "retrieval" in query_lower:
        query_vector[10:20] += 0.5
    if "augmented" in query_lower:
        query_vector[20:30] += 0.5
    if "generation" in query_lower:
        query_vector[30:40] += 0.5

    # Normalize the vector
    return query_vector / np.linalg.norm(query_vector)


def get_embedding_ollama(query_text, model):
    """Get embedding from Ollama API."""
    url = "http://localhost:11434/api/embeddings"
    payload = {"model": model, "prompt": query_text}
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("embedding")


def find_top_matches(tweets, query_text, embedding_type, top_k=10):
    """Find top k matches using cosine similarity."""
    similarities = []

    # Get a reference vector to determine query vector

    # Create query vector
    if embedding_type == "nomic":
        query_vector = get_embedding_ollama(query_text, "nomic-embed-text:latest")
    elif embedding_type == "gemma":
        query_vector = get_embedding_ollama(query_text, "embeddinggemma:latest")
    else:
        raise ValueError(f"Invalid embedding type: {embedding_type}")

    # Calculate similarities
    for tweet_id, tweet_data in tweets.items():
        embeddings = tweet_data.get("embeddings", {})
        if embedding_type in embeddings and embeddings[embedding_type] is not None:
            tweet_embedding = np.array(embeddings[embedding_type])
            similarity = cosine_similarity_numpy(query_vector, tweet_embedding)
            similarities.append((similarity, tweet_id, tweet_data))

    # Sort by similarity (descending)
    similarities.sort(reverse=True)

    return similarities[:top_k]


def search_tweets(file_path, query):
    """Main function to search tweets."""
    print(f"Searching for query: '{query}'")
    print("=" * 50)

    # Load tweets
    tweets = load_tweets(file_path)
    print(f"Total tweets loaded: {len(tweets)}")

    # Count tweets with embeddings
    nomic_count, gemma_count, both_count = count_tweets_with_embeddings(tweets)
    print(f"Tweets with nomic embeddings: {nomic_count}")
    print(f"Tweets with gemma embeddings: {gemma_count}")
    print(f"Tweets with both embeddings: {both_count}")
    print()

    # Get embedding dimensions
    sample_tweet = next(iter(tweets.values()))
    nomic_dim = (
        len(sample_tweet["embeddings"]["nomic"])
        if sample_tweet["embeddings"]["nomic"]
        else 0
    )
    gemma_dim = (
        len(sample_tweet["embeddings"]["gemma"])
        if sample_tweet["embeddings"]["gemma"]
        else 0
    )

    print(f"Nomic embedding dimension: {nomic_dim}")
    print(f"Gemma embedding dimension: {gemma_dim}")
    print()

    # Search using nomic embeddings
    if nomic_count > 0:
        print("TOP 10 MATCHES USING NOMIC EMBEDDINGS:")
        print("=" * 40)
        nomic_matches = find_top_matches(tweets, query, "nomic", 10)
        for i, (similarity, tweet_id, tweet_data) in enumerate(nomic_matches, 1):
            content = tweet_data["content"]
            print(f"{i}. Similarity: {similarity:.4f}")
            print(f"   Author: {tweet_data['author']}")
            print(f"   Content: {content}")
            print(f"   ID: {tweet_id}")
            print()

    # Search using gemma embeddings
    if gemma_count > 0:
        print("TOP 10 MATCHES USING GEMMA EMBEDDINGS:")
        print("=" * 40)
        gemma_matches = find_top_matches(tweets, query, "gemma", 10)
        for i, (similarity, tweet_id, tweet_data) in enumerate(gemma_matches, 1):
            content = tweet_data["content"]
            print(f"{i}. Similarity: {similarity:.4f}")
            print(f"   Author: {tweet_data['author']}")
            print(f"   Content: {content}")
            print(f"   ID: {tweet_id}")
            print()


if __name__ == "__main__":
    import sys

    # Default query
    query = "RAG"

    # Check if query was provided as command line argument
    if len(sys.argv) > 1:
        query = sys.argv[1]

    # Run the search
    search_tweets("combined_tweets.json", query)
