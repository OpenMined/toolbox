#!/usr/bin/env python3
"""Script to download Discord users to JSON file."""

import asyncio
import os
import sys
from typing import Optional

from discord_downloader.api import download_users


def get_env_var(name: str, default: Optional[str] = None) -> str:
    """Get environment variable or raise error if required."""
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is required")
    return value


async def main():
    """Main function to download users."""
    try:
        # Get configuration from environment variables
        token = get_env_var("DISCORD_TOKEN")
        guild_name = get_env_var("DISCORD_GUILD_NAME")
        output_dir = get_env_var("OUTPUT_DIR", "/tmp")
        
        print(f"Downloading users from '{guild_name}'")
        print(f"Output directory: {output_dir}")
        
        # Download users
        output_path = await download_users(
            token=token,
            guild_name=guild_name,
            output_dir=output_dir,
        )
        
        print(f"Users downloaded successfully to: {output_path}")
        
    except Exception as e:
        print(f"Error downloading users: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())