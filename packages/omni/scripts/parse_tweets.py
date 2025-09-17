#!/usr/bin/env python3
"""
Script to parse all tweet JSON files from ../../data/ directory
and create a simple JSON with format: {tweet_id: {author: author_name, content: full_text}}
"""

import json
from pathlib import Path


def extract_tweets_from_file(file_path):
    """Extract tweets from a single JSON file."""
    tweets = {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate the Twitter API response structure
        if (
            "data" in data
            and "home" in data["data"]
            and "home_timeline_urt" in data["data"]["home"]
        ):
            instructions = data["data"]["home"]["home_timeline_urt"].get(
                "instructions", []
            )

            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    entries = instruction.get("entries", [])

                    for entry in entries:
                        # Handle conversation entries
                        if (
                            "content" in entry
                            and entry["content"].get("entryType")
                            == "TimelineTimelineModule"
                        ):
                            items = entry["content"].get("items", [])

                            for item in items:
                                if "item" in item and "itemContent" in item["item"]:
                                    item_content = item["item"]["itemContent"]

                                    if item_content.get("itemType") == "TimelineTweet":
                                        tweet_results = item_content.get(
                                            "tweet_results", {}
                                        )

                                        if "result" in tweet_results:
                                            result = tweet_results["result"]

                                            # Extract tweet data
                                            tweet_id = result.get("rest_id")
                                            if not tweet_id:
                                                continue

                                            # Get author info
                                            author = "Unknown"
                                            if (
                                                "core" in result
                                                and "user_results" in result["core"]
                                            ):
                                                user_result = result["core"][
                                                    "user_results"
                                                ].get("result", {})
                                                if "core" in user_result:
                                                    author = user_result["core"].get(
                                                        "screen_name", "Unknown"
                                                    )

                                            # Get tweet content
                                            content = ""
                                            if "legacy" in result:
                                                content = result["legacy"].get(
                                                    "full_text", ""
                                                )
                                            elif "note_tweet" in result:
                                                # Handle long tweets
                                                note_results = result["note_tweet"].get(
                                                    "note_tweet_results", {}
                                                )
                                                if "result" in note_results:
                                                    content = note_results[
                                                        "result"
                                                    ].get("text", "")

                                            if tweet_id and content:
                                                tweets[tweet_id] = {
                                                    "author": author,
                                                    "content": content,
                                                }

                        # Handle direct tweet entries
                        elif (
                            "content" in entry
                            and entry["content"].get("entryType")
                            == "TimelineTimelineItem"
                        ):
                            item_content = entry["content"].get("itemContent", {})

                            if item_content.get("itemType") == "TimelineTweet":
                                tweet_results = item_content.get("tweet_results", {})

                                if "result" in tweet_results:
                                    result = tweet_results["result"]

                                    # Extract tweet data
                                    tweet_id = result.get("rest_id")
                                    if not tweet_id:
                                        continue

                                    # Get author info
                                    author = "Unknown"
                                    if (
                                        "core" in result
                                        and "user_results" in result["core"]
                                    ):
                                        user_result = result["core"][
                                            "user_results"
                                        ].get("result", {})
                                        if "core" in user_result:
                                            author = user_result["core"].get(
                                                "screen_name", "Unknown"
                                            )

                                    # Get tweet content
                                    content = ""
                                    if "legacy" in result:
                                        content = result["legacy"].get("full_text", "")
                                    elif "note_tweet" in result:
                                        # Handle long tweets
                                        note_results = result["note_tweet"].get(
                                            "note_tweet_results", {}
                                        )
                                        if "result" in note_results:
                                            content = note_results["result"].get(
                                                "text", ""
                                            )

                                    if tweet_id and content:
                                        tweets[tweet_id] = {
                                            "author": author,
                                            "content": content,
                                        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return tweets


def main():
    """Main function to process all JSON files and combine tweets."""
    data_dir = Path("../../data/")

    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist!")
        return

    # Find all JSON files in the data directory
    json_files = list(data_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {data_dir}")
        return

    print(f"Found {len(json_files)} JSON files to process...")

    # Combine all tweets
    all_tweets = {}

    for json_file in json_files:
        print(f"Processing {json_file.name}...")
        tweets = extract_tweets_from_file(json_file)
        all_tweets.update(tweets)
        print(f"  Found {len(tweets)} tweets")

    print(f"\nTotal unique tweets extracted: {len(all_tweets)}")

    # Write the combined tweets to output file
    output_file = "combined_tweets.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_tweets, f, indent=2, ensure_ascii=False)

    print(f"Combined tweets saved to {output_file}")


if __name__ == "__main__":
    main()
