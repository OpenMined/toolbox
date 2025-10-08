import json

# Load your JSON response (replace with your variable or file)
with open("home_latest_timeline.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = []

# Navigate to the entries
entries = data["data"]["home"]["home_timeline_urt"]["instructions"][0]["entries"]

for entry in entries:
    content = entry.get("content", {})
    item_content = content.get("itemContent", {})

    # Skip if not a Tweet
    if item_content.get("__typename") != "TimelineTweet":
        continue

    tweet = item_content["tweet_results"]["result"]
    user = tweet["core"]["user_results"]["result"]

    # Extract details
    name = user["core"]["name"]
    handle = "@" + user["core"]["screen_name"]
    date = tweet["legacy"]["created_at"]
    likes = tweet["legacy"].get("favorite_count", 0)
    retweets = tweet["legacy"].get("retweet_count", 0)
    text = tweet["legacy"]["full_text"]

    # "Reactions" = likes + retweets + replies + quotes + bookmarks
    reactions = (
        likes
        + retweets
        + tweet["legacy"].get("reply_count", 0)
        + tweet["legacy"].get("quote_count", 0)
        + tweet["legacy"].get("bookmark_count", 0)
    )

    results.append(
        {
            "name": name,
            "handle": handle,
            "date": date,
            "likes": likes,
            "retweets": retweets,
            "reactions": reactions,
            "text": text,
        }
    )

# Example: print results
for r in results:
    print(r)
