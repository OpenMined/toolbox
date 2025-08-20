"""
Discord MCP

A Python package for downloading Discord messages, users, and channel data
using the Discord REST API with rate limiting and retry logic.
"""

from pathlib import Path

from discord_mcp.api import (
    download_channels,
    download_guilds,
    download_messages,
    download_messages_with_users,
)
from discord_mcp.client import DiscordClient

# Path constants for accessing test assets and repo root
DISCORD_PACKAGE_PATH = Path(__file__).parent
DISCORD_REPO_PATH = DISCORD_PACKAGE_PATH.parent

__version__ = "1.0.0"
__all__ = [
    "DiscordClient",
    "download_messages",
    "download_messages_with_users",
    "download_channels",
    "download_guilds",
    "DISCORD_PACKAGE_PATH",
    "DISCORD_REPO_PATH",
]
