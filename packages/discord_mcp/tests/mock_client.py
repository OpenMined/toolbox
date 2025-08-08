"""Mock Discord client for testing that inherits from real client but mocks API calls."""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import copy

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
            use_permissions_data: Whether to prefer permissions test data over original data
            **kwargs: Additional arguments passed to parent DiscordClient
        """
        # Initialize parent without creating HTTP session
        self.token = token
        self.rate_limit_preference = kwargs.get(
            "rate_limit_preference", RateLimitPreference.RESPECT_ALL
        )
        self._resolved_token_kind: Optional[TokenKind] = None
        self._session = None  # No HTTP session needed

        # Load test data for mocking API responses
        self.test_assets_path = Path(__file__).parent / "test_assets"
        self._test_data = {
            "messages": self._load_test_data("messages_test_data.json"),
            "messages_with_users": self._load_test_data(
                "messages_with_users_test_data.json"
            ),
            "channels": self._load_test_data("channels_test_data.json"),
            "users_from_channel": self._load_test_data(
                "users_from_channel_test_data.json"
            ),
            "guilds": self._load_test_data("guilds_test_data.json"),
            # Permission-related test data
            "permissions_current_user": self._load_test_data(
                "permissions_current_user.json"
            ),
            "permissions_user_guilds": self._load_test_data(
                "permissions_user_guilds.json"
            ),
            "permissions_member_roles": self._load_test_data(
                "permissions_member_roles.json"
            ),
            "permissions_guild_roles": self._load_test_data(
                "permissions_guild_roles.json"
            ),
            "permissions_guild_channels": self._load_test_data(
                "permissions_guild_channels.json"
            ),
            "permissions_guild_info": self._load_test_data(
                "permissions_guild_info.json"
            ),
        }

    def _load_test_data(self, filename: str) -> Dict[str, Any]:
        """Load test data from JSON file."""
        file_path = self.test_assets_path / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def close(self):
        """Mock close method - no HTTP session to close."""
        pass

    def get_messages_since(
        self, channel_id: str, since: datetime, until=None, before=None
    ):
        """Override get_messages_since to handle test data with dynamic timestamp patching."""
        # Get messages from test data
        messages_data = self._test_data.get("messages", {})
        if "messages" not in messages_data:
            return iter([])

        all_messages = messages_data["messages"]
        
        # Determine the time window
        if until is None:
            until = since + timedelta(hours=24)  # Default to 24 hours if no until specified
            
        # Convert since/until to UTC if they're naive
        if since.tzinfo is None:
            since = since.replace(tzinfo=datetime.now().astimezone().tzinfo)
        if until.tzinfo is None:
            until = until.replace(tzinfo=since.tzinfo)
            
        # Calculate time span for distributing messages
        time_span = until - since
        
        # Take a subset of messages to work with (limit to reasonable number)
        messages_to_use = all_messages[:100]  # Use first 100 messages
        
        if not messages_to_use:
            return iter([])
            
        # Create patched messages with timestamps distributed between since and until
        patched_messages = []
        for i, message in enumerate(messages_to_use):
            # Create a deep copy to avoid modifying original test data
            patched_message = copy.deepcopy(message)
            
            # Calculate new timestamp: distribute messages evenly across the time span
            progress = i / max(1, len(messages_to_use) - 1) if len(messages_to_use) > 1 else 0
            new_timestamp = since + timedelta(seconds=time_span.total_seconds() * progress)
            
            # Format timestamp in Discord's ISO format
            patched_message["timestamp"] = new_timestamp.isoformat().replace("+00:00", "Z")
            
            patched_messages.append(patched_message)
            
        return iter(patched_messages)

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
        if "?" in endpoint:
            endpoint_path, query_string = endpoint.split("?", 1)
            params = parse_qs(query_string)
        else:
            endpoint_path = endpoint
            params = {}

        # Mock responses based on endpoint
        if endpoint_path == "users/@me":
            # Return current user info - prefer permissions data if available
            permissions_user = self._test_data.get("permissions_current_user", {})
            if permissions_user:
                return permissions_user

            # Fallback to guild data or default
            guilds_data = self._test_data.get("guilds", {})
            if "metadata" in guilds_data and "user" in guilds_data["metadata"]:
                return guilds_data["metadata"]["user"]
            return {
                "id": "140257135190632465",
                "username": "test_user",
                "discriminator": "0000",
            }

        elif endpoint_path == "users/@me/guilds":
            # Return paginated guilds - use permissions data if requested, otherwise original
            guilds = self._test_data.get("permissions_user_guilds", [])
            return guilds

        elif endpoint_path == "users/@me/channels":
            # Return DM channels (empty for our test data)
            return []

        elif endpoint_path.startswith("guilds/") and endpoint_path.endswith(
            "/channels"
        ):
            # Return channels for a guild - use permissions data if requested, otherwise original

            permissions_channels = self._test_data.get("permissions_guild_channels", [])
            return permissions_channels

        elif endpoint_path.startswith("guilds/") and "/members/" in endpoint_path:
            # Return member info (for get_member_roles)
            # Expected format: guilds/{guild_id}/members/{user_id}
            path_parts = endpoint_path.split("/")
            if len(path_parts) >= 4 and path_parts[2] == "members":
                user_id = path_parts[3]
                # Return member roles from permissions test data
                member_roles = self._test_data.get("permissions_member_roles", [])
                return {"user": {"id": user_id}, "roles": member_roles, "nick": None}
            return {}

        elif endpoint_path.startswith("guilds/") and endpoint_path.endswith("/roles"):
            # Return guild roles (for get_guild_roles)
            guild_roles_dict = self._test_data.get("permissions_guild_roles", {})
            if guild_roles_dict:
                # Convert dict back to list format for API response
                return list(guild_roles_dict.values())
            return []

        elif endpoint_path.startswith("guilds/"):
            # Return guild info
            guild_id = endpoint_path.split("/")[1]

            # Prefer permissions guild info if available
            permissions_guild = self._test_data.get("permissions_guild_info", {})
            if permissions_guild and permissions_guild.get("id") == guild_id:
                return permissions_guild

            # Fallback to original guild data
            guilds_data = self._test_data.get("guilds", {})
            if "guilds" in guilds_data:
                for guild in guilds_data["guilds"]:
                    if guild["id"] == guild_id:
                        return guild

            # Return mock guild if not found
            return {"id": guild_id, "name": "Test Guild", "icon": None}

        elif endpoint_path.startswith("channels/") and "/messages" in endpoint_path:
            # Return messages for a channel
            messages_data = self._test_data.get("messages", {})
            if "messages" in messages_data:
                messages = messages_data["messages"]

                # Handle pagination parameters
                after = params.get("after", [None])[0]
                before = params.get("before", [None])[0]
                limit = int(params.get("limit", ["100"])[0])

                # Filter messages based on after/before
                filtered_messages = messages
                if after:
                    filtered_messages = [
                        m for m in filtered_messages if m["id"] > after
                    ]
                if before:
                    filtered_messages = [
                        m for m in filtered_messages if m["id"] < before
                    ]

                # Apply limit and return (Discord returns newest first)
                return filtered_messages[:limit]
            return []

        elif endpoint_path.startswith("channels/"):
            # Return channel info
            channel_id = endpoint_path.split("/")[1]
            channels_data = self._test_data.get("channels", {})
            if "channels" in channels_data:
                for channel in channels_data["channels"]:
                    if channel["id"] == channel_id:
                        return channel
            # Return mock channel if not found
            return {"id": channel_id, "name": "test-channel", "type": 0}

        elif endpoint_path.startswith("users/"):
            # Return user info
            user_id = endpoint_path.split("/")[1]

            # Look in messages with users data first
            messages_with_users_data = self._test_data.get("messages_with_users", {})
            if "users" in messages_with_users_data:
                for user in messages_with_users_data["users"]:
                    if user["id"] == user_id:
                        return user

            # Look in users from channel data
            users_data = self._test_data.get("users_from_channel", {})
            if "users" in users_data:
                for user in users_data["users"]:
                    if user["id"] == user_id:
                        return user

            # User not found - raise NotFoundException like real API would
            raise NotFoundException(f"Request to 'users/{user_id}' failed: not found")

        else:
            # Unknown endpoint
            raise NotFoundException(f"Request to '{endpoint}' failed: not found")
