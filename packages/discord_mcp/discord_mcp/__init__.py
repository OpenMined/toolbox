"""
Discord Downloader

A Python package for downloading Discord messages, users, and channel data
using the Discord REST API with rate limiting and retry logic.
"""

from discord_downloader.client import DiscordClient
from discord_downloader.api import download_messages, download_users, download_channels

__version__ = "1.0.0"
__all__ = ["DiscordClient", "download_messages", "download_users", "download_channels"]