#!/usr/bin/env python3
"""Script to download Discord messages to JSON file."""

import asyncio
import os
import sys
from typing import Optional

from discord_downloader.api import download_messages


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Get environment variable or raise error if required."""
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is required")
    return value


async def main():
    """Main function to download messages."""
    try:
        # Get configuration from environment variables
        token = get_env_var("DISCORD_TOKEN")
        guild_name = get_env_var("DISCORD_GUILD_NAME")
        channel_name = get_env_var("DISCORD_CHANNEL_NAME")
        output_dir = get_env_var("OUTPUT_DIR", "/tmp")
        days_back = int(get_env_var("DAYS_BACK", "365"))
        
        print(f"Downloading messages from '{guild_name}' -> '{channel_name}'")
        print(f"Going back {days_back} days")
        print(f"Output directory: {output_dir}")
        
        # Download messages
        output_path = await download_messages(
            token=token,
            guild_name=guild_name,
            channel_name=channel_name,
            output_dir=output_dir,
            days_back=days_back,
        )
        
        print(f"Messages downloaded successfully to: {output_path}")
        
    except Exception as e:
        print(f"Error downloading messages: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())