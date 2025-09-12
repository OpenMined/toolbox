import math
import os
import sys
import time
from datetime import datetime

from slack_sdk import WebClient
from toolbox_events import send_event
from tqdm import tqdm

from slack_mcp.db import (
    get_earliest_timestamp_from_db,
    get_latest_timestamp_from_db,
    get_slack_connection,
    upsert_message,
)
from slack_mcp.overview_utils import (
    get_channel_messages_with_thread_tree,
    get_my_active_channels_from_search,
)

token = os.getenv("SLACK_TOKEN")
d_cookie = os.getenv("SLACK_D_COOKIE")


def get_timestamp_batches(from_ts, to_ts, batch_days=30):
    batch_seconds = batch_days * 24 * 60 * 60

    n_batches = math.ceil((to_ts - from_ts) / batch_seconds)
    for i in range(n_batches):
        start = from_ts + i * batch_seconds
        end = start + batch_seconds
        yield (start, end)


def get_messages_from_channels(client, channel_ids, from_ts=None, to_ts=None):
    all_messages_as_tree = []
    all_messaages_flat = []

    for channel in tqdm(channel_ids):
        message_tree = get_channel_messages_with_thread_tree(
            client, channel, max_pages=100, oldest=from_ts, latest=to_ts
        )
        all_messages_as_tree.extend(message_tree)
        print(f"Got {len(message_tree)} messages for channel {channel}")

    for message in all_messages_as_tree:
        to_add = [message] + message.get("replies", [])
        for msg in to_add:
            msg["channel_id"] = channel
        all_messaages_flat.extend(to_add)

    return all_messaages_flat


def get_webclient():
    headers = {
        "Cookie": f"d={d_cookie}",
        "User-Agent": "Mozilla/5.0 (compatible; Python)",
    }
    return WebClient(token=token, headers=headers)


def run_slack_mesage_dump_background_worker_single(
    conn,
    client,
    min_ts,
    min_batch_length,
):
    print("getting active channels", file=sys.stderr)

    n_days_since_min_ts = (time.time() - min_ts) // (24 * 60 * 60)
    channel_ids = get_my_active_channels_from_search(
        client, last_n_days=n_days_since_min_ts, max_pages=100
    )
    earliest_message_ts = get_earliest_timestamp_from_db(conn)
    latest_message_ts = get_latest_timestamp_from_db(conn)

    if earliest_message_ts is None:
        earliest_message_ts = math.inf
        latest_message_ts = -math.inf

    # get the time batches from now until min_ts, and check if its in the range
    now = time.time()
    for batch_start, batch_end in get_timestamp_batches(min_ts, now, batch_days=30):
        batch_end = min(batch_end, time.time())

        date_str_start = datetime.fromtimestamp(batch_start).strftime("%Y-%m-%d")
        date_str_end = datetime.fromtimestamp(batch_end).strftime("%Y-%m-%d")

        print(
            f"Processing batch from {date_str_start} to {date_str_end} for {len(channel_ids)} channels",
            file=sys.stderr,
        )

        batch_length = batch_end - batch_start
        if batch_length < min_batch_length:
            # skip this batch, too short
            print(
                f"Skipping batch {date_str_start} to {date_str_end} because it's too short"
            )
            continue

        if batch_start >= earliest_message_ts and batch_end <= latest_message_ts:
            # skip this batch, already indexed
            print(
                f"Skipping batch {date_str_start} to {date_str_end} because it's already indexed"
            )
            continue

        # Truncate batch_start to only get new messages
        if latest_message_ts > batch_start:
            # Add small offset to exclude the last message we already have
            batch_start = latest_message_ts + 1e-6
            print(
                f"Truncating batch to only fetch messages after {datetime.fromtimestamp(batch_start).strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # Skip if batch is empty after truncation
        if batch_start >= batch_end:
            print("Skipping batch - no new messages to fetch")
            continue

        # TODO: this is probably more efficient with search?
        all_messages_flat = get_messages_from_channels(
            client,
            channel_ids,
            from_ts=batch_start,
            to_ts=batch_end,
        )

        print(f"Got {len(all_messages_flat)} messages, adding to db")
        for msg in all_messages_flat:
            # TODO: fix threading here
            # skip bot messages for now
            if "user" not in msg:
                continue
            upsert_message(conn, msg)

        send_new_message_batch_event(all_messages_flat, batch_start, batch_end)


def send_new_message_batch_event(all_messages, batch_start, batch_end):
    # Only send event if batch_start is shorter than 10 minutes ago
    if batch_start < time.time() - 10 * 60:
        return

    # skip bot messages
    messages_filtered = [msg for msg in all_messages if "user" in msg]
    if len(messages_filtered) == 0:
        return

    print(f"Sending event for {len(messages_filtered)} new messages", file=sys.stderr)

    send_event(
        "slack.message.new_batch",
        {
            "messages": messages_filtered,
            "batch_start": batch_start,
            "batch_end": batch_end,
        },
    )


def run_slack_mesage_dump_background_worker_loop():
    # check what the last timestamp is locally
    sleep_interval = 60
    min_ts = time.time() - 1 * 24 * 60 * 60  # one year ago

    with get_slack_connection() as conn:
        client = get_webclient()

        while True:
            run_slack_mesage_dump_background_worker_single(
                conn,
                client,
                min_ts,
                min_batch_length=sleep_interval,
            )
            time.sleep(sleep_interval)
