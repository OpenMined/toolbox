#!/usr/bin/env python3
"""
Script to generate embeddings for tweets using ToolboxStore.
"""

import os
import sys

from tqdm import tqdm

# Add the parent directory to the path so we can import from omni
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omni.db import get_tweet_store


def main():
    """Generate embeddings for all tweets without embeddings using ToolboxStore."""
    print("Generating embeddings for tweets using ToolboxStore...")

    store = get_tweet_store()
    print(f"Connected to ToolboxStore at {store.db.db_path}")

    batch_size = 1000
    total_processed = 0

    # First, get total count of docs without embeddings for progress bar
    total_docs = len(
        store.db.get_docs_without_embeddings(limit=10000)
    )  # Get a large number to estimate total

    with tqdm(total=total_docs, desc="Creating embeddings") as pbar:
        while True:
            # Get documents without embeddings in batches
            docs_without_embeddings = store.db.get_docs_without_embeddings(
                limit=batch_size
            )

            if not docs_without_embeddings:
                break

            # Create embeddings and chunks for these documents
            chunks = store.embed_documents(docs_without_embeddings)

            # Insert the chunks (which includes embeddings)
            store.insert_chunks(chunks)

            total_processed += len(docs_without_embeddings)
            pbar.update(len(docs_without_embeddings))

            # If we got fewer documents than batch_size, we're done
            if len(docs_without_embeddings) < batch_size:
                break

    if total_processed == 0:
        print("✓ All tweets already have embeddings!")
    else:
        print(
            f"✓ Embedding generation complete! Processed {total_processed} tweets total."
        )


if __name__ == "__main__":
    main()
