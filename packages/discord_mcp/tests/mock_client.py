"""Mock Discord client for testing that inherits from real client but mocks API calls."""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from discord_mcp import DISCORD_PACKAGE_PATH
from discord_mcp.client import DiscordClient, TokenKind, RateLimitPreference
from discord_mcp.exceptions import NotFoundException


class MockDiscordClient(DiscordClient):
    """Mock Discord client that inherits from real client but uses test data instead of making HTTP requests.
    
    This approach reuses all the business logic from DiscordClient (pagination, data processing, 
    error handling, etc.) but mocks only the HTTP calls by overriding _make_request.
    """
    
    def __init__(self, token: str = "mock_token", **kwargs):
        """Initialize mock client with test data.
        
        Args:
            token: Mock token (ignored)
            **kwargs: Additional arguments passed to parent DiscordClient
        """
        # Initialize parent without creating HTTP session
        self.token = token
        self.rate_limit_preference = kwargs.get('rate_limit_preference', RateLimitPreference.RESPECT_ALL)
        self._resolved_token_kind: Optional[TokenKind] = None
        self._session = None  # No HTTP session needed
        
        # Load test data for mocking API responses
        self.test_assets_path = DISCORD_PACKAGE_PATH / "test_assets"
        self._test_data = {
            'messages': self._load_test_data("messages_test_data.json"),
            'messages_with_users': self._load_test_data("messages_with_users_test_data.json"), 
            'channels': self._load_test_data("channels_test_data.json"),
            'users_from_channel': self._load_test_data("users_from_channel_test_data.json"),
            'guilds': self._load_test_data("guilds_test_data.json"),
        }
        
    def _load_test_data(self, filename: str) -> Dict[str, Any]:
        """Load test data from JSON file."""
        file_path = self.test_assets_path / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def close(self):
        """Mock close method - no HTTP session to close."""
        pass
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        token_kind: Optional[TokenKind] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Mock the HTTP request by returning test data based on the endpoint.
        
        This method maps Discord API endpoints to our test data, allowing the real
        business logic in the parent class methods to process the data naturally.
        """
        # Parse URL to extract endpoint and parameters
        if '?' in endpoint:
            endpoint_path, query_string = endpoint.split('?', 1)
            params = parse_qs(query_string)
        else:
            endpoint_path = endpoint
            params = {}
            
        # Mock responses based on endpoint
        if endpoint_path == "users/@me":
            # Return current user info
            guilds_data = self._test_data.get('guilds', {})
            if 'metadata' in guilds_data and 'user' in guilds_data['metadata']:
                return guilds_data['metadata']['user']
            return {
                "id": "140257135190632465",
                "username": "test_user", 
                "discriminator": "0000"
            }
            
        elif endpoint_path == "users/@me/guilds":
            # Return paginated guilds
            guilds_data = self._test_data.get('guilds', {})
            if 'guilds' in guilds_data:
                guilds = guilds_data['guilds']
                # Handle pagination
                after = params.get('after', ['0'])[0]
                limit = int(params.get('limit', ['100'])[0])
                
                # Simple pagination simulation
                if after == '0':
                    return guilds[:limit]
                else:
                    # Find index of 'after' guild and return next batch
                    start_idx = 0
                    for i, guild in enumerate(guilds):
                        if guild['id'] == after:
                            start_idx = i + 1
                            break
                    return guilds[start_idx:start_idx + limit]
            return []
            
        elif endpoint_path == "users/@me/channels":
            # Return DM channels (empty for our test data)
            return []
            
        elif endpoint_path.startswith("guilds/") and endpoint_path.endswith("/channels"):
            # Return channels for a guild
            channels_data = self._test_data.get('channels', {})
            if 'channels' in channels_data:
                return channels_data['channels']
            return []
            
        elif endpoint_path.startswith("guilds/"):
            # Return guild info
            guild_id = endpoint_path.split('/')[1]
            guilds_data = self._test_data.get('guilds', {})
            if 'guilds' in guilds_data:
                for guild in guilds_data['guilds']:
                    if guild['id'] == guild_id:
                        return guild
            # Return mock guild if not found
            return {
                "id": guild_id,
                "name": "Test Guild",
                "icon": None
            }
            
        elif endpoint_path.startswith("channels/") and "/messages" in endpoint_path:
            # Return messages for a channel
            messages_data = self._test_data.get('messages', {})
            if 'messages' in messages_data:
                messages = messages_data['messages']
                
                # Handle pagination parameters
                after = params.get('after', [None])[0]
                before = params.get('before', [None])[0] 
                limit = int(params.get('limit', ['100'])[0])
                
                # Filter messages based on after/before
                filtered_messages = messages
                if after:
                    filtered_messages = [m for m in filtered_messages if m['id'] > after]
                if before:
                    filtered_messages = [m for m in filtered_messages if m['id'] < before]
                    
                # Apply limit and return (Discord returns newest first)
                return filtered_messages[:limit]
            return []
            
        elif endpoint_path.startswith("channels/"):
            # Return channel info
            channel_id = endpoint_path.split('/')[1]
            channels_data = self._test_data.get('channels', {})
            if 'channels' in channels_data:
                for channel in channels_data['channels']:
                    if channel['id'] == channel_id:
                        return channel
            # Return mock channel if not found
            return {
                "id": channel_id,
                "name": "test-channel",
                "type": 0
            }
            
        elif endpoint_path.startswith("users/"):
            # Return user info
            user_id = endpoint_path.split('/')[1]
            
            # Look in messages with users data first
            messages_with_users_data = self._test_data.get('messages_with_users', {})
            if 'users' in messages_with_users_data:
                for user in messages_with_users_data['users']:
                    if user['id'] == user_id:
                        return user
                        
            # Look in users from channel data
            users_data = self._test_data.get('users_from_channel', {})
            if 'users' in users_data:
                for user in users_data['users']:
                    if user['id'] == user_id:
                        return user
                        
            # User not found - raise NotFoundException like real API would
            raise NotFoundException(f"Request to 'users/{user_id}' failed: not found")
            
        else:
            # Unknown endpoint
            raise NotFoundException(f"Request to '{endpoint}' failed: not found")