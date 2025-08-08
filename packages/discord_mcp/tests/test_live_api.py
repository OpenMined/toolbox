"""Live tests for Discord API functionality."""

import os

import pytest
from discord_mcp.api import download_messages, download_channels, download_users_from_channel


@pytest.mark.live
def test_download_messages_live():
    """Test downloading messages from Discord API with live data."""
    # Get token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        pytest.skip("DISCORD_TOKEN environment variable not set")
    
    # Test parameters
    guild_name = "Claude Developers"
    channel_name = "general"
    days_back = 1
    
    # Call the download function
    result = download_messages(
        token=token,
        guild_name=guild_name,
        channel_name=channel_name,
        days_back=days_back,
    )
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "messages" in result
    
    # Verify metadata
    metadata = result["metadata"]
    assert "guild" in metadata
    assert "channel" in metadata
    assert "message_count" in metadata
    assert "export_date" in metadata
    assert "date_range" in metadata
    
    # Verify messages
    messages = result["messages"]
    assert isinstance(messages, list)
    assert metadata["message_count"] == len(messages)
    
    print(f"Successfully downloaded {len(messages)} messages")
    print(f"Guild: {metadata['guild']['name']}")
    print(f"Channel: {metadata['channel']['name']}")


@pytest.mark.live
def test_download_channels_live():
    """Test downloading channels from Discord API with live data."""
    # Get token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        pytest.skip("DISCORD_TOKEN environment variable not set")
    
    # Test parameters
    guild_name = "Claude Developers"
    
    # Call the download function
    result = download_channels(
        token=token,
        guild_name=guild_name,
    )
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "channels" in result
    
    # Verify metadata
    metadata = result["metadata"]
    assert "guild" in metadata
    assert "channel_count" in metadata
    assert "export_date" in metadata
    
    # Verify channels
    channels = result["channels"]
    assert isinstance(channels, list)
    assert metadata["channel_count"] == len(channels)
    assert len(channels) > 0  # Should have at least some channels
    
    # Check that each channel has expected fields
    for channel in channels:
        assert "id" in channel
        assert "type" in channel
        # name might not exist for all channel types
    
    print(f"Successfully downloaded {len(channels)} channels")
    print(f"Guild: {metadata['guild']['name']}")


@pytest.mark.live
def test_download_users_from_channel_live():
    """Test downloading users from a Discord channel with live data."""
    # Get token from environment
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        pytest.skip("DISCORD_TOKEN environment variable not set")
    
    # Test parameters
    guild_name = "Claude Developers"
    channel_name = "general"
    
    # Call the download function
    result = download_users_from_channel(
        token=token,
        guild_name=guild_name,
        channel_name=channel_name,
    )
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "users" in result
    
    # Verify metadata
    metadata = result["metadata"]
    assert "guild" in metadata
    assert "channel" in metadata
    assert "user_count" in metadata
    assert "export_date" in metadata
    
    # Verify users
    users = result["users"]
    assert isinstance(users, list)
    assert metadata["user_count"] == len(users)
    
    # Check that each user has expected fields
    for user in users:
        assert "id" in user
        assert "username" in user
    
    print(f"Successfully downloaded {len(users)} users")
    print(f"Guild: {metadata['guild']['name']}")
    print(f"Channel: {metadata['channel']['name']}")