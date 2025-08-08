"""API functions for downloading Discord data to JSON files."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any

from discord_mcp.client import DiscordClient
from datetime import UTC


def download_messages(
    token: str,
    guild_name: str,
    channel_name: str,
    days_back: int = 365,
) -> Dict[str, Any]:
    """Download messages from a Discord channel.

    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        channel_name: Name of the channel to download messages from
        days_back: Number of days back to download messages (default: 365 for 1 year)

    Returns:
        Dictionary containing messages and metadata
    """
    client = DiscordClient(token)
    try:
        # Find the guild by name
        guild_id = None
        guild_info = None
        for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break

        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")

        # Find the channel by name
        channel_id = None
        channel_info = None
        for channel in client.get_guild_channels(guild_id):
            if channel.get("name", "").lower() == channel_name.lower():
                channel_id = channel["id"]
                channel_info = channel
                break

        if not channel_id:
            raise ValueError(
                f"Channel '{channel_name}' not found in guild '{guild_name}'"
            )

        # Calculate the date to start fetching from
        since_date = datetime.now(UTC) - timedelta(days=days_back)

        # Collect all messages
        messages = []
        for message in client.get_messages_since(channel_id, since_date):
            messages.append(message)

        # Prepare and return data
        return {
            "metadata": {
                "guild": guild_info,
                "channel": channel_info,
                "export_date": datetime.now(UTC).isoformat() + "Z",
                "message_count": len(messages),
                "date_range": {
                    "since": since_date.isoformat() + "Z",
                    "until": datetime.now(UTC).isoformat() + "Z",
                },
            },
            "messages": messages,
        }
    finally:
        client.close()


def download_messages_with_users(
    token: str,
    guild_name: str,
    channel_name: str,
    days_back: int = 365,
) -> Dict[str, Any]:
    """Download messages from a Discord channel along with user data.

    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        channel_name: Name of the channel to download messages from
        days_back: Number of days back to download messages (default: 365 for 1 year)

    Returns:
        Dictionary containing messages, users, and metadata
    """
    client = DiscordClient(token)
    try:
        # Find the guild by name
        guild_id = None
        guild_info = None
        for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break

        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")

        # Find the channel by name
        channel_id = None
        channel_info = None
        for channel in client.get_guild_channels(guild_id):
            if channel.get("name", "").lower() == channel_name.lower():
                channel_id = channel["id"]
                channel_info = channel
                break

        if not channel_id:
            raise ValueError(
                f"Channel '{channel_name}' not found in guild '{guild_name}'"
            )

        # Calculate the date to start fetching from
        since_date = datetime.now(UTC) - timedelta(days=days_back)

        # Collect messages and build user cache on-demand
        messages = []
        user_cache: Dict[str, Optional[Dict]] = {}
        unique_user_ids: Set[str] = set()

        for message in client.get_messages_since(channel_id, since_date):
            messages.append(message)

            # Collect user IDs from message authors
            author_id = message["author"]["id"]
            unique_user_ids.add(author_id)

            # Collect user IDs from mentions
            for mention in message.get("mentions", []):
                unique_user_ids.add(mention["id"])

            # Collect user IDs from reactions
            for reaction in message.get("reactions", []):
                # Note: reaction users would need separate API calls to get full list
                pass

        # Fetch user details for all unique users found in messages
        print(
            f"Found {len(unique_user_ids)} unique users in messages, fetching user details..."
        )
        for user_id in unique_user_ids:
            if user_id not in user_cache:
                try:
                    user_info = client.get_user(user_id)
                    user_cache[user_id] = user_info
                except Exception as e:
                    print(f"Could not fetch user {user_id}: {e}")
                    user_cache[user_id] = None

        # Filter out None values and collect valid users
        users = [user for user in user_cache.values() if user is not None]

        # Prepare and return data
        return {
            "metadata": {
                "guild": guild_info,
                "channel": channel_info,
                "export_date": datetime.now(UTC).isoformat() + "Z",
                "message_count": len(messages),
                "user_count": len(users),
                "date_range": {
                    "since": since_date.isoformat() + "Z",
                    "until": datetime.now(UTC).isoformat() + "Z",
                },
            },
            "messages": messages,
            "users": users,
        }
    finally:
        client.close()


def download_channels(
    token: str,
    guild_name: str,
) -> Dict[str, Any]:
    """Download channel information from a Discord server.

    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild

    Returns:
        Dictionary containing channels and metadata
    """
    client = DiscordClient(token)
    try:
        # Find the guild by name
        guild_id = None
        guild_info = None
        for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break

        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")

        # Get detailed guild information
        if guild_id != "@me":
            guild_info = client.get_guild(guild_id)

        # Collect all channels
        channels = []
        for channel in client.get_guild_channels(guild_id):
            channels.append(channel)

        # Prepare and return data
        return {
            "metadata": {
                "guild": guild_info,
                "export_date": datetime.now(UTC).isoformat() + "Z",
                "channel_count": len(channels),
            },
            "channels": channels,
        }
    finally:
        client.close()


def download_users_from_channel(
    token: str,
    guild_name: str,
    channel_name: str,
) -> Dict[str, Any]:
    """Download all users from a Discord channel.

    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        channel_name: Name of the channel to get users from

    Returns:
        Dictionary containing users and metadata
    """
    client = DiscordClient(token)
    try:
        # Find the guild by name
        guild_id = None
        guild_info = None
        for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break

        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")

        # Find the channel by name
        channel_id = None
        channel_info = None
        for channel in client.get_guild_channels(guild_id):
            if channel.get("name", "").lower() == channel_name.lower():
                channel_id = channel["id"]
                channel_info = channel
                break

        if not channel_id:
            raise ValueError(
                f"Channel '{channel_name}' not found in guild '{guild_name}'"
            )

        # Get detailed guild information
        if guild_id != "@me":
            guild_info = client.get_guild(guild_id)

        # Get all messages from the channel to find users who have participated
        print(
            f"Fetching messages from channel '{channel_name}' to collect user information..."
        )
        user_cache: Dict[str, Dict] = {}

        # Get all messages and collect user information directly from message data
        for message in client.get_messages(channel_id, limit=10000):
            # Collect user info from message authors
            author = message["author"]
            user_cache[author["id"]] = author

            # Collect user info from mentions (they already contain user data)
            for mention in message.get("mentions", []):
                user_cache[mention["id"]] = mention

        # Convert to list
        users = list(user_cache.values())
        print(f"Found {len(users)} unique users in channel")

        # Prepare and return data
        return {
            "metadata": {
                "guild": guild_info,
                "channel": channel_info,
                "export_date": datetime.now(UTC).isoformat() + "Z",
                "user_count": len(users),
            },
            "users": users,
        }
    finally:
        client.close()


def download_guilds(
    token: str,
) -> Dict[str, Any]:
    """Download all guilds (servers) for the authenticated user.

    Args:
        token: Discord token

    Returns:
        Dictionary containing guilds and metadata
    """
    client = DiscordClient(token)

    try:
        # Get current user info
        user_info = client.get_current_user()

        # Collect all guilds
        guilds = []
        for guild in client.get_user_guilds():
            guilds.append(guild)

        # Prepare and return data
        return {
            "metadata": {
                "user": user_info,
                "export_date": datetime.now(UTC).isoformat() + "Z",
                "guild_count": len(guilds),
            },
            "guilds": guilds,
        }
    finally:
        client.close()
