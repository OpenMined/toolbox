import time
from datetime import datetime, timedelta

from slack_sdk.errors import SlackApiError


def get_my_active_channels_from_search(client, last_n_days=7, max_pages=50):
    active_channel_ids = set()
    current_page = 1
    after_date = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y-%m-%d")
    query = f"after:{after_date}"  # filter messages after this date
    MAX_RATE_LIMIT_RETRIES = 20
    rate_limit_retries = 0
    while current_page <= max_pages:
        try:
            response = client.search_messages(
                query=query,
                sort="timestamp",
                sort_dir="desc",
                count=100,
                page=current_page,
            )

            matches = response["messages"]["matches"]
            for match in matches:
                channel_id = match["channel"]["id"]
                active_channel_ids.add(channel_id)

            paging = response["messages"].get("paging", {})
            total_pages = paging.get("pages", 1)

            if current_page >= total_pages:
                break

            current_page += 1

        except SlackApiError as e:
            if (
                e.response["error"] == "ratelimited"
                and rate_limit_retries < MAX_RATE_LIMIT_RETRIES
            ):
                rate_limit_retries += 1
                print(
                    "Got rate limited by slack, sleeping for 60 seconds and continuing"
                )
                time.sleep(60)
            else:
                print(f"Slack API Error: {e.response}")
                break

    return list(active_channel_ids)


def get_channel_messages(client, channel_id, oldest=None, latest=None, max_pages=50):
    messages = []
    cursor = None
    current_page = 1
    MAX_RATE_LIMIT_RETRIES = 20
    rate_limit_retries = 0
    while current_page <= max_pages:
        try:
            history = client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                latest=latest,
                limit=1000,
                cursor=cursor,
                page=current_page,
            )
            messages.extend(history["messages"])
            current_page += 1
            cursor = history.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        except SlackApiError as e:
            if (
                e.response["error"] == "ratelimited"
                and rate_limit_retries < MAX_RATE_LIMIT_RETRIES
            ):
                rate_limit_retries += 1
                print(
                    "Got rate limited by slack, sleeping for 60 seconds and continuing"
                )
                time.sleep(60)
            else:
                raise e
    return messages


def get_conversations_replies(client, channel_id, ts, limit=1000, max_pages=50):
    current_page = 1
    replies = []
    MAX_RATE_LIMIT_RETRIES = 20
    rate_limit_retries = 0
    while current_page <= max_pages:
        try:
            replies_result = client.conversations_replies(
                channel=channel_id, ts=ts, limit=limit
            )
            # Skip the first message (it's the same as the parent)
            replies.extend(replies_result["messages"][1:])
            current_page += 1
            cursor = replies_result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        except SlackApiError as e:
            if (
                e.response["error"] == "ratelimited"
                and rate_limit_retries < MAX_RATE_LIMIT_RETRIES
            ):
                rate_limit_retries += 1
                print(
                    "Got rate limited by slack, sleeping for 60 seconds and continuing"
                )
                time.sleep(60)
            else:
                raise e
    return replies


def get_channel_messages_with_thread_tree(
    client, channel_id, oldest=None, latest=None, max_pages=50
):
    messages = []
    cursor = None
    current_page = 1
    MAX_RATE_LIMIT_RETRIES = 20
    rate_limit_retries = 0
    while current_page <= max_pages:
        try:
            history = client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                latest=latest,
                limit=1000,
                cursor=cursor,
            )

            for message in history["messages"]:
                # Initialize thread replies as an empty list
                message["replies"] = []

                # Check if the message starts a thread
                if "thread_ts" in message and message.get("reply_count", 0) > 0:
                    replies = get_conversations_replies(
                        client,
                        channel_id,
                        message["thread_ts"],
                        limit=100,
                        max_pages=20,
                    )
                    message["replies"].extend(replies)

                messages.append(message)

            cursor = history.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        except SlackApiError as e:
            if (
                e.response["error"] == "ratelimited"
                and rate_limit_retries < MAX_RATE_LIMIT_RETRIES
            ):
                rate_limit_retries += 1
                print(
                    "Got rate limited by slack, sleeping for 60 seconds and continuing"
                )
                time.sleep(60)
            else:
                raise e

    return messages


def get_last_week_messages(client, channel_ids):
    messages_by_channel = {}
    one_week_ago = datetime.now() - timedelta(days=7)
    oldest_ts = time.mktime(one_week_ago.timetuple())
    for channel_id in channel_ids:
        messages_by_channel[channel_id] = get_channel_messages_with_thread_tree(
            client, channel_id, oldest_ts
        )
    return messages_by_channel


def get_last_week_messages_with_names(
    client, channel_ids, channelid_to_name, userid_to_name
):
    messages_by_channel = get_last_week_messages(client, channel_ids)
    for channel_id, messages in messages_by_channel.items():
        for message in messages:
            message["channel_name"] = channelid_to_name[channel_id]
            message["user_name"] = userid_to_name.get(
                message.get("user", None), "Unknown User"
            )
    return messages_by_channel


def get_last_week_messages_with_threads_with_names(
    client, channel_ids, channelid_to_name, userid_to_name
):
    messages_by_channel = get_last_week_messages(client, channel_ids)
    for channel_id, messages in messages_by_channel.items():
        for message in messages:
            message["channel_name"] = channelid_to_name[channel_id]
            message["user_name"] = userid_to_name.get(
                message.get("user", None), "Unknown User"
            )
            # If there are replies/threads, add channel_name and user_name to each reply
            if "replies" in message and isinstance(message["replies"], list):
                for reply in message["replies"]:
                    reply["channel_name"] = channelid_to_name[channel_id]
                    reply["user_name"] = userid_to_name.get(
                        reply.get("user", None), "Unknown User"
                    )

    return messages_by_channel
