"""API functions for downloading Discord data to JSON files."""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from discord_downloader.client import DiscordClient


async def download_messages(
    token: str,
    guild_name: str,
    channel_name: str,
    output_dir: str = "/tmp",
    days_back: int = 365,
) -> str:
    """Download messages from a Discord channel to a JSON file.
    
    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        channel_name: Name of the channel to download messages from
        output_dir: Directory to save the JSON file
        days_back: Number of days back to download messages (default: 365 for 1 year)
    
    Returns:
        Path to the created JSON file
    """
    async with DiscordClient(token) as client:
        # Find the guild by name
        guild_id = None
        guild_info = None
        async for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break
        
        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")
        
        # Find the channel by name
        channel_id = None
        channel_info = None
        async for channel in client.get_guild_channels(guild_id):
            if channel.get("name", "").lower() == channel_name.lower():
                channel_id = channel["id"]
                channel_info = channel
                break
        
        if not channel_id:
            raise ValueError(f"Channel '{channel_name}' not found in guild '{guild_name}'")
        
        # Calculate the date to start fetching from
        since_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Collect all messages
        messages = []
        async for message in client.get_messages_since(channel_id, since_date):
            messages.append(message)
        
        # Prepare output data
        output_data = {
            "metadata": {
                "guild": guild_info,
                "channel": channel_info,
                "export_date": datetime.utcnow().isoformat() + "Z",
                "message_count": len(messages),
                "date_range": {
                    "since": since_date.isoformat() + "Z",
                    "until": datetime.utcnow().isoformat() + "Z",
                },
            },
            "messages": messages,
        }
        
        # Save to JSON file
        os.makedirs(output_dir, exist_ok=True)
        filename = f"messages_{guild_name}_{channel_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path


async def download_users(
    token: str,
    guild_name: str,
    output_dir: str = "/tmp",
) -> str:
    """Download user information from a Discord server to a JSON file.
    
    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        output_dir: Directory to save the JSON file
    
    Returns:
        Path to the created JSON file
    """
    async with DiscordClient(token) as client:
        # Find the guild by name
        guild_id = None
        guild_info = None
        async for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break
        
        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")
        
        # Get current user info
        current_user = await client.get_current_user()
        
        # Collect unique user IDs from recent messages across all channels
        user_ids: Set[str] = set()
        user_ids.add(current_user["id"])  # Add current user
        
        # Sample messages from all accessible channels to find users
        async for channel in client.get_guild_channels(guild_id):
            if channel.get("type") in [0, 2, 5]:  # Text, voice, announcement channels
                try:
                    # Get recent messages to extract user IDs
                    message_count = 0
                    async for message in client.get_messages(channel["id"], limit=100):
                        user_ids.add(message["author"]["id"])
                        # Also add mentioned users
                        for mention in message.get("mentions", []):
                            user_ids.add(mention["id"])
                        message_count += 1
                        if message_count >= 100:  # Limit per channel
                            break
                except Exception as e:
                    print(f"Could not access channel {channel.get('name', channel['id'])}: {e}")
                    continue
        
        # Fetch user details
        users = []
        for user_id in user_ids:
            try:
                user_info = await client.get_user(user_id)
                if user_info:
                    users.append(user_info)
            except Exception as e:
                print(f"Could not fetch user {user_id}: {e}")
                continue
        
        # Prepare output data
        output_data = {
            "metadata": {
                "guild": guild_info,
                "export_date": datetime.utcnow().isoformat() + "Z",
                "user_count": len(users),
                "current_user": current_user,
            },
            "users": users,
        }
        
        # Save to JSON file
        os.makedirs(output_dir, exist_ok=True)
        filename = f"users_{guild_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path


async def download_channels(
    token: str,
    guild_name: str,
    output_dir: str = "/tmp",
) -> str:
    """Download channel information from a Discord server to a JSON file.
    
    Args:
        token: Discord token
        guild_name: Name of the Discord server/guild
        output_dir: Directory to save the JSON file
    
    Returns:
        Path to the created JSON file
    """
    async with DiscordClient(token) as client:
        # Find the guild by name
        guild_id = None
        guild_info = None
        async for guild in client.get_user_guilds():
            if guild["name"].lower() == guild_name.lower():
                guild_id = guild["id"]
                guild_info = guild
                break
        
        if not guild_id:
            raise ValueError(f"Guild '{guild_name}' not found")
        
        # Get detailed guild information
        if guild_id != "@me":
            guild_info = await client.get_guild(guild_id)
        
        # Collect all channels
        channels = []
        async for channel in client.get_guild_channels(guild_id):
            channels.append(channel)
        
        # Prepare output data
        output_data = {
            "metadata": {
                "guild": guild_info,
                "export_date": datetime.utcnow().isoformat() + "Z",
                "channel_count": len(channels),
            },
            "channels": channels,
        }
        
        # Save to JSON file
        os.makedirs(output_dir, exist_ok=True)
        filename = f"channels_{guild_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path