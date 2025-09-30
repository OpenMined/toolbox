from typing import Any

from omni.vectorstore_models import Tweet


def parse_user_tweets_json(data: Any) -> list[Tweet]:
    """Parse tweets from JSON data structure."""
    instructions = (
        data.get("data", {})
        .get("user", {})
        .get("result", {})
        .get("timeline", {})
        .get("timeline", {})
        .get("instructions", [])
    )
    return parse_tweets_from_instructions(instructions)


def parse_tweets_json(data: Any) -> list[Tweet]:
    """Parse tweets from JSON data structure."""

    # Navigate through the JSON structure and find all tweet_results
    # data user result timeline timeline instructions
    instructions = (
        data.get("data", {})
        .get("home", {})
        .get("home_timeline_urt", {})
        .get("instructions", [])
    )
    return parse_tweets_from_instructions(instructions)


def parse_tweets_from_instructions(instructions: list[Any]) -> list[Tweet]:
    all_tweets = []
    seen_tweet_ids = set()
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

            # Handle direct tweet entries (TimelineTimelineItem)
            elif content.get("entryType") == "TimelineTimelineItem":
                item_content = content.get("itemContent", {})
                if item_content.get("itemType") == "TimelineTweet":
                    tweet_results = item_content.get("tweet_results", {})
                    tweet = Tweet.from_instruction_entry(tweet_results)
                    if tweet and tweet.tweet_id not in seen_tweet_ids:
                        seen_tweet_ids.add(tweet.tweet_id)
                        all_tweets.append(tweet)

    return all_tweets
