"""Unit tests for Discord API functionality using mock client."""

import pytest
from unittest.mock import patch

from discord_mcp.api import (
    download_messages, 
    download_messages_with_users,
    download_channels,
    download_users_from_channel,
    download_guilds
)
from tests.mock_client import MockDiscordClient


class TestDownloadMessages:
    """Test download_messages function with mock data."""
    
    @patch('discord_mcp.api.DiscordClient', MockDiscordClient)
    def test_download_messages_structure(self):
        """Test that download_messages returns expected structure."""
        result = download_messages(
            token="mock_token",
            guild_name="Claude Developers", 
            channel_name="general",
            days_back=7  # Use 7 days to ensure we get test messages
        )
        
        # Verify structure
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
        assert len(messages) > 0, "Messages list should not be empty - mock should return test data"
        assert len(messages) >= 10, f"Expected some test data, got only {len(messages)} messages"
        assert metadata["message_count"] == len(messages)
        
        # Verify message structure
        message = messages[0]
        assert "id" in message
        assert "content" in message
        assert "author" in message
        assert "timestamp" in message
    
    @patch('discord_mcp.api.DiscordClient', MockDiscordClient)
    def test_download_messages_with_users_structure(self):
        """Test that download_messages_with_users returns expected structure."""
        result = download_messages_with_users(
            token="mock_token",
            guild_name="Claude Developers",
            channel_name="general",
            days_back=7  # Use 7 days to ensure we get test messages
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "messages" in result
        assert "users" in result
        
        # Verify metadata
        metadata = result["metadata"]
        assert "guild" in metadata
        assert "channel" in metadata
        assert "message_count" in metadata
        assert "user_count" in metadata
        assert "export_date" in metadata
        assert "date_range" in metadata
        
        # Verify messages and users
        messages = result["messages"]
        users = result["users"]
        assert isinstance(messages, list)
        assert isinstance(users, list)
        assert len(messages) > 0, "Messages list should not be empty - mock should return test data"
        assert len(users) > 0, "Users list should not be empty - mock should return test data"
        assert metadata["message_count"] == len(messages)
        assert metadata["user_count"] == len(users)


class TestDownloadChannels:
    """Test download_channels function with mock data."""
    
    @patch('discord_mcp.api.DiscordClient', MockDiscordClient)
    def test_download_channels_structure(self):
        """Test that download_channels returns expected structure."""
        result = download_channels(
            token="mock_token",
            guild_name="Claude Developers"
        )
        
        # Verify structure
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
        assert len(channels) > 0, "Channels list should not be empty - mock should return test data"
        assert len(channels) >= 10, f"Expected substantial test data, got only {len(channels)} channels"
        assert metadata["channel_count"] == len(channels)
        
        # Verify channel structure
        channel = channels[0]
        assert "id" in channel
        assert "type" in channel


class TestDownloadUsersFromChannel:
    """Test download_users_from_channel function with mock data."""
    
    @patch('discord_mcp.api.DiscordClient', MockDiscordClient)
    def test_download_users_from_channel_structure(self):
        """Test that download_users_from_channel returns expected structure."""
        result = download_users_from_channel(
            token="mock_token",
            guild_name="Claude Developers",
            channel_name="general"
        )
        
        # Verify structure
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
        assert len(users) > 0, "Users list should not be empty - mock should return test data"
        assert len(users) >= 5, f"Expected substantial test data, got only {len(users)} users"
        assert metadata["user_count"] == len(users)
        
        # Verify user structure
        user = users[0]
        assert "id" in user
        assert "username" in user


class TestDownloadGuilds:
    """Test download_guilds function with mock data."""
    
    @patch('discord_mcp.api.DiscordClient', MockDiscordClient)
    def test_download_guilds_structure(self):
        """Test that download_guilds returns expected structure."""
        result = download_guilds(token="mock_token")
        
        # Verify structure
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "guilds" in result
        
        # Verify metadata
        metadata = result["metadata"]
        assert "user" in metadata
        assert "guild_count" in metadata
        assert "export_date" in metadata
        
        # Verify guilds
        guilds = result["guilds"]
        assert isinstance(guilds, list)
        assert len(guilds) > 0, "Guilds list should not be empty - mock should return test data"
        assert metadata["guild_count"] == len(guilds)
        
        # Verify guild structure
        guild = guilds[0]
        assert "id" in guild
        assert "name" in guild


class TestMockDiscordClient:
    """Test MockDiscordClient functionality."""
    
    def test_mock_client_initialization(self):
        """Test that MockDiscordClient initializes correctly."""
        client = MockDiscordClient("test_token")
        
        assert client.token == "test_token"
        assert client.test_assets_path.exists()
    
    def test_mock_client_context_manager(self):
        """Test that MockDiscordClient works as context manager."""
        with MockDiscordClient("test_token") as client:
            assert client is not None
            user = client.get_current_user()
            assert isinstance(user, dict)
            assert "id" in user
    
    def test_mock_client_get_user_guilds(self):
        """Test that get_user_guilds returns mock data."""
        client = MockDiscordClient("test_token")
        
        guilds = list(client.get_user_guilds())
        assert isinstance(guilds, list)
        assert len(guilds) > 0, "Mock client should return non-empty guilds list from test data"
        
        # Verify guild structure
        guild = guilds[0]
        assert "id" in guild
        assert "name" in guild
    
    def test_mock_client_get_messages(self):
        """Test that get_messages returns mock data."""
        client = MockDiscordClient("test_token")
        
        messages = list(client.get_messages("test_channel_id"))
        assert isinstance(messages, list)
        assert len(messages) > 0, "Mock client should return non-empty messages list from test data"
        
        # Verify message structure
        message = messages[0]
        assert "id" in message
        assert "content" in message
        assert "author" in message
    
    def test_mock_client_get_guild_channels(self):
        """Test that get_guild_channels returns mock data."""
        client = MockDiscordClient("test_token")
        
        channels = list(client.get_guild_channels("test_guild_id"))
        assert isinstance(channels, list)
        assert len(channels) > 0, "Mock client should return non-empty channels list from test data"
        
        # Verify channel structure
        channel = channels[0]
        assert "id" in channel
        assert "type" in channel