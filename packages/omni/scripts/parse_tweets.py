#!/usr/bin/env python3
"""
Script to parse all tweet JSON files from ../../data/ directory
and store them using ToolboxStore
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from omni
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omni.db import get_tweet_store
from omni.vectorstore_models import Tweet


def main():
    """Main function to process all JSON files and store tweets using ToolboxStore."""

    data_dir = Path().home() / "workspace" / "toolbox" / "data"

    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist!")
        return

    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {data_dir}")
        return

    print(f"Found {len(json_files)} JSON files to process...")

    store = get_tweet_store()
    print(f"Initialized ToolboxStore at {store.db.db_path}")

    # Drop tweets table to recreate with new schema
    store.db.conn.execute("DROP TABLE IF EXISTS tweets_documents")
    store.db.conn.commit()
    print("Dropped existing tweets table")

    # Force schema creation
    store.db.create_schema()
    print("Recreated tables with new schema")

    all_tweets = []
    seen_tweet_ids = set()

    for json_file in json_files:
        print(f"Processing {json_file.name}...")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        file_tweet_count = 0

        # Navigate through the JSON structure and find all tweet_results
        instructions = (
            data.get("data", {})
            .get("home", {})
            .get("home_timeline_urt", {})
            .get("instructions", [])
        )

        for instruction in instructions:
            if instruction.get("type") != "TimelineAddEntries":
                continue

            entries = instruction.get("entries", [])

            for entry in entries:
                content = entry.get("content", {})
                # Handle conversation entries (TimelineTimelineModule)
                if content.get("entryType") == "TimelineTimelineModule":
                    items = content.get("items", [])
                    for item in items:
                        item_content = item.get("item", {}).get("itemContent", {})
                        if item_content.get("itemType") == "TimelineTweet":
                            tweet_results = item_content.get("tweet_results", {})
                            tweet = Tweet.from_instruction_entry(tweet_results)
                            if tweet and tweet.tweet_id not in seen_tweet_ids:
                                seen_tweet_ids.add(tweet.tweet_id)
                                all_tweets.append(tweet)
                                file_tweet_count += 1

                # Handle direct tweet entries (TimelineTimelineItem)
                elif content.get("entryType") == "TimelineTimelineItem":
                    item_content = content.get("itemContent", {})
                    if item_content.get("itemType") == "TimelineTweet":
                        tweet_results = item_content.get("tweet_results", {})
                        tweet = Tweet.from_instruction_entry(tweet_results)
                        if tweet and tweet.tweet_id not in seen_tweet_ids:
                            seen_tweet_ids.add(tweet.tweet_id)
                            all_tweets.append(tweet)
                            file_tweet_count += 1

        print(f"  Found {file_tweet_count} tweets")

    print(f"\nTotal unique tweets extracted: {len(all_tweets)}")

    if all_tweets:
        print("Inserting tweets into ToolboxStore...")
        store.insert_docs(all_tweets, create_embeddings=False)
        print(f"Successfully inserted {len(all_tweets)} tweets into ToolboxStore")


if __name__ == "__main__":
    main()
