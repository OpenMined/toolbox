import time
from datetime import datetime, timedelta

from slack_sdk.errors import SlackApiError


def get_my_active_channels_from_search(client, last_n_days=7, max_pages=50):
    active_channel_ids = set()
    current_page = 1
    after_date = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y-%m-%d")
    query = f"after:{after_date}"  # filter messages after this date

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
            print(f"Slack API Error: {e.response['error']}")
            break

    return list(active_channel_ids)


def get_channel_messages(client, channel_id, oldest=None, latest=None):
    try:
        messages = []
        cursor = None
        while True:
            history = client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                latest=latest,
                limit=1000,
                cursor=cursor,
            )
            messages.extend(history["messages"])
            cursor = history.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return messages

    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")


def get_channel_messages_with_thread_tree(client, channel_id, oldest=None, latest=None):
    try:
        messages = []
        cursor = None

        while True:
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
                    replies = client.conversations_replies(
                        channel=channel_id, ts=message["thread_ts"]
                    )
                    # Skip the first message (it's the same as the parent)
                    thread_replies = replies["messages"][1:]
                    message["replies"].extend(thread_replies)

                messages.append(message)

            cursor = history.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return messages

    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")


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
