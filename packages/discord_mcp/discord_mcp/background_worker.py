import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

from discord_mcp.client import DiscordClient
from discord_mcp.db import (
    get_discord_connection,
    get_earliest_timestamp_from_db,
    get_latest_timestamp_from_db,
    upsert_message,
    upsert_user,
    upsert_channel,
    upsert_guild,
    get_message_count,
)
from discord_mcp.models import DiscordMessage, DiscordUser, DiscordChannel, DiscordGuild


def get_discord_client():
    """Create Discord client with token from environment"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is required")
    return DiscordClient(token)


def parse_discord_timestamp(timestamp_str: str) -> datetime:
    """Parse Discord timestamp string to datetime object"""
    # Discord timestamps are in format: "2025-08-06T09:23:32.955000+00:00"
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def datetime_to_discord_timestamp(dt: datetime) -> str:
    """Convert datetime to Discord timestamp string"""
    iso_string = dt.isoformat()
    if iso_string.endswith("+00:00"):
        return iso_string.replace("+00:00", "Z")
    else:
        return iso_string + "Z"


def get_time_windows_to_fetch(
    earliest_ts: Optional[str], latest_ts: Optional[str], days_back: int = 365
) -> List[tuple[datetime, datetime]]:
    """
    Get time windows that need to be fetched, avoiding already indexed ranges.

    Args:
        earliest_ts: Earliest message timestamp in database (ISO string)
        latest_ts: Latest message timestamp in database (ISO string)
        days_back: Number of days to go back from now

    Returns:
        List of (start_time, end_time) tuples to fetch
    """
    # Use timezone-aware datetime from the start
    now = datetime.now(timezone.utc)
    min_time = now - timedelta(days=days_back)

    windows = []

    if earliest_ts is None or latest_ts is None:
        # No data in database, fetch everything
        windows.append((min_time, now))
    else:
        earliest_dt = parse_discord_timestamp(earliest_ts)
        latest_dt = parse_discord_timestamp(latest_ts)

        # Fetch newer messages (from latest_dt to now)
        if latest_dt < now:
            windows.append((latest_dt, now))

        # Fetch older messages (from min_time to earliest_dt)
        if earliest_dt > min_time:
            windows.append((min_time, earliest_dt))

    return windows


def run_discord_mesage_download_and_write_background_worker_single(
    conn, client: DiscordClient, guild_names: List[str] = None, days_back: int = 100
):
    """
    Download Discord messages from specified guilds or all accessible guilds.

    Args:
        conn: Database connection
        client: Discord API client
        guild_names: List of guild names to process, or None for all guilds
        days_back: Number of days to go back from now (default: 100)
    """
    print("Starting Discord message dump background worker")

    # Get guilds to process
    all_guilds = list(client.get_user_guilds())
    if guild_names:
        guilds_to_process = [g for g in all_guilds if g["name"] in guild_names]
        print(f"Processing specific guilds: {guild_names}")
    else:
        guilds_to_process = all_guilds
        print(f"Processing all {len(guilds_to_process)} accessible guilds")

    if not guilds_to_process:
        print("No guilds found to process")
        return

    # Get time windows that need to be fetched
    earliest_message_ts = get_earliest_timestamp_from_db(conn)
    latest_message_ts = get_latest_timestamp_from_db(conn)

    print(f"Database message range: {earliest_message_ts} to {latest_message_ts}")

    windows_to_fetch = get_time_windows_to_fetch(
        earliest_message_ts, latest_message_ts, days_back
    )

    if not windows_to_fetch:
        print("No new time windows to fetch")
        return

    print(f"Will fetch {len(windows_to_fetch)} time windows")

    # Process each guild
    for guild_info in guilds_to_process:
        guild_id = guild_info["id"]
        guild_name = guild_info["name"]

        print(f"\nProcessing guild: {guild_name} ({guild_id})")

        # Upsert guild info
        try:
            # Get detailed guild info if not DM
            if guild_id != "@me":
                detailed_guild = client.get_guild(guild_id)
                guild_model = DiscordGuild(**detailed_guild)
                upsert_guild(conn, guild_model)

            # Get channels for this guild
            channels = list(client.get_guild_channels(guild_id))
            print(f"Found {len(channels)} channels in guild {guild_name}")

            # Process each channel
            for channel_info in channels:
                channel_id = channel_info["id"]
                channel_name = channel_info.get("name", f"Channel-{channel_id}")
                channel_type = channel_info.get("type", 0)

                # Skip voice channels and categories
                if channel_type not in [0, 1, 5, 10, 11, 12]:  # Text channel types
                    continue

                print(f"  Processing channel: {channel_name} ({channel_id})")

                # Upsert channel info
                channel_model = DiscordChannel(**channel_info)
                upsert_channel(conn, channel_model)

                # Process each time window for this channel
                for start_time, end_time in windows_to_fetch:
                    print(f"    Fetching messages from {start_time} to {end_time}")

                    try:
                        # Get messages in this time window
                        message_count = 0
                        user_cache: Dict[str, DiscordUser] = {}

                        for message_data in client.get_messages_since(
                            channel_id, start_time, until=end_time
                        ):
                            message_count += 1

                            # Process message author
                            if "author" in message_data and message_data["author"]:
                                author_data = message_data["author"]
                                author_id = author_data["id"]

                                if author_id not in user_cache:
                                    user_model = DiscordUser(**author_data)
                                    user_cache[author_id] = user_model

                            # Process mentioned users
                            for mention in message_data.get("mentions", []):
                                user_id = mention["id"]
                                if user_id not in user_cache:
                                    user_model = DiscordUser(**mention)
                                    user_cache[user_id] = user_model

                            # Create and store message
                            message_model = DiscordMessage.from_discord_api(
                                message_data
                            )
                            upsert_message(conn, message_model)

                        # Upsert all users found in this batch
                        for user_model in user_cache.values():
                            upsert_user(conn, user_model)

                        if message_count > 0:
                            print(
                                f"    Added {message_count} messages and {len(user_cache)} users"
                            )

                    except Exception as e:
                        print(
                            f"    Error fetching messages for channel {channel_name}: {e}"
                        )
                        continue

        except Exception as e:
            print(f"Error processing guild {guild_name}: {e}")
            continue

    total_messages = get_message_count(conn)
    print(
        f"\nBackground worker completed. Total messages in database: {total_messages}"
    )


def run_discord_mesage_download_and_write_background_worker_loop(
    guild_names: List[str] = None, sleep_interval: int = 300, days_back: int = 100
):
    """
    Run the Discord message dump background worker in a continuous loop.

    Args:
        guild_names: List of guild names to process, or None for all guilds
        sleep_interval: Time to sleep between runs in seconds (default: 5 minutes)
        days_back: Number of days to go back from now (default: 100)
    """
    print(
        f"Starting Discord message dump background worker loop (sleep interval: {sleep_interval}s)"
    )

    while True:
        try:
            with get_discord_connection() as conn:
                client = get_discord_client()
                try:
                    run_discord_mesage_download_and_write_background_worker_single(
                        conn, client, guild_names, days_back
                    )
                finally:
                    client.close()

            print(f"Sleeping for {sleep_interval} seconds...")
            time.sleep(sleep_interval)

        except KeyboardInterrupt:
            print("Background worker stopped by user")
            break
        except Exception as e:
            print(f"Error in background worker loop: {e}")
            print(f"Retrying in {sleep_interval} seconds...")
            time.sleep(sleep_interval)
