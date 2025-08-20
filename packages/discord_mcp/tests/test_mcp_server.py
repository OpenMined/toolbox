"""Unit tests for Discord MCP server functionality."""

from datetime import datetime, timedelta

from discord_mcp.db import (
    get_discord_connection,
    upsert_channel,
    upsert_guild,
    upsert_message,
    upsert_user,
)
from discord_mcp.mcp_server import (
    get_channels,
    get_history,
    get_last_messages_in_my_channels,
    get_user_id_for_name,
    get_users,
)
from discord_mcp.models import DiscordChannel, DiscordGuild, DiscordMessage, DiscordUser

from tests.utils import get_random_tmp_file


class TestMCPServer:
    """Test Discord MCP server functions."""

    def setup_method(self):
        """Setup test database with sample data for each test."""
        self.test_db_path = get_random_tmp_file().with_suffix(".sqlite")

        # Populate test data
        with get_discord_connection(self.test_db_path) as conn:
            self._populate_test_data(conn)

    def teardown_method(self):
        """Cleanup after each test."""
        if self.test_db_path.exists():
            self.test_db_path.unlink()

    def _populate_test_data(self, conn):
        """Populate database with test data: 5 users, 5 messages, 1 guild, 2 channels."""

        # Create 1 guild
        guild = DiscordGuild(
            id="123456789012345678",
            name="Test Guild",
            icon="test_icon",
            description="A test Discord guild",
            owner_id="100000000000000001",
        )
        upsert_guild(conn, guild)

        # Create 2 channels
        channel1 = DiscordChannel(
            id="200000000000000001",
            type=0,  # Text channel
            guild_id="123456789012345678",
            name="general",
            topic="General discussion",
        )
        channel2 = DiscordChannel(
            id="200000000000000002",
            type=0,  # Text channel
            guild_id="123456789012345678",
            name="random",
            topic="Random chat",
        )
        upsert_channel(conn, channel1)
        upsert_channel(conn, channel2)

        # Create 5 users
        users = []
        for i in range(5):
            user = DiscordUser(
                id=f"10000000000000000{i + 1}",
                username=f"testuser{i + 1}",
                global_name=f"Test User {i + 1}",
                discriminator="0001"
                if i < 4
                else None,  # Newer users might not have discriminator
                avatar=f"avatar_{i + 1}",
            )
            users.append(user)
            upsert_user(conn, user)

        # Create 5 messages (3 in channel1, 2 in channel2)
        now = datetime.now()
        messages = []

        for i in range(5):
            channel_id = "200000000000000001" if i < 3 else "200000000000000002"
            user_idx = i % 5
            message_time = now - timedelta(days=i + 1)  # Messages from 1-5 days ago

            message = DiscordMessage(
                id=f"30000000000000000{i + 1}",
                channel_id=channel_id,
                author_id=f"10000000000000000{user_idx + 1}",
                content=f"This is test message {i + 1}",
                timestamp=message_time.isoformat(),
                type=0,  # Regular message
            )
            messages.append(message)
            upsert_message(conn, message)

    def test_get_channels(self):
        """Test getting all channels."""
        with get_discord_connection(self.test_db_path) as conn:  # noqa: F841
            # Temporarily patch the db connection in the mcp_server module
            import discord_mcp.mcp_server as mcp_module

            original_get_connection = mcp_module.db.get_discord_connection
            mcp_module.db.get_discord_connection = lambda: get_discord_connection(
                self.test_db_path
            )

            try:
                result = get_channels()

                assert "channels" in result
                channels = result["channels"]
                assert len(channels) == 2

                # Check channel names
                channel_names = {ch["name"] for ch in channels}
                assert channel_names == {"general", "random"}

                # Check data structure
                for channel in channels:
                    assert "id" in channel
                    assert "name" in channel
                    assert "type" in channel
                    assert "guild_id" in channel

            finally:
                mcp_module.db.get_discord_connection = original_get_connection

    def test_get_users(self):
        """Test getting all users."""
        with get_discord_connection(self.test_db_path) as conn:  # noqa: F841
            # Temporarily patch the db connection
            import discord_mcp.mcp_server as mcp_module

            original_get_connection = mcp_module.db.get_discord_connection
            mcp_module.db.get_discord_connection = lambda: get_discord_connection(
                self.test_db_path
            )

            try:
                result = get_users()

                assert "users" in result
                users = result["users"]
                assert len(users) == 5

                # Check usernames
                usernames = {user["username"] for user in users}
                expected_usernames = {f"testuser{i}" for i in range(1, 6)}
                assert usernames == expected_usernames

                # Check data structure
                for user in users:
                    assert "id" in user
                    assert "username" in user
                    assert "global_name" in user

            finally:
                mcp_module.db.get_discord_connection = original_get_connection

    def test_get_last_messages_in_my_channels(self):
        """Test getting recent messages from all channels."""
        with get_discord_connection(self.test_db_path) as conn:  # noqa: F841
            # Temporarily patch the db connection
            import discord_mcp.mcp_server as mcp_module

            original_get_connection = mcp_module.db.get_discord_connection
            mcp_module.db.get_discord_connection = lambda: get_discord_connection(
                self.test_db_path
            )

            try:
                result = get_last_messages_in_my_channels(last_n_days=7)

                assert "messages" in result
                messages = result["messages"]
                assert len(messages) == 5

                # Check message content
                contents = {msg["content"] for msg in messages}
                expected_contents = {f"This is test message {i}" for i in range(1, 6)}
                assert contents == expected_contents

                # Check data structure
                for message in messages:
                    assert "id" in message
                    assert "channel_id" in message
                    assert "author_id" in message
                    assert "content" in message
                    assert "timestamp" in message

            finally:
                mcp_module.db.get_discord_connection = original_get_connection

    def test_get_history(self):
        """Test getting channel history."""
        with get_discord_connection(self.test_db_path) as conn:  # noqa: F841
            # Temporarily patch the db connection
            import discord_mcp.mcp_server as mcp_module

            original_get_connection = mcp_module.db.get_discord_connection
            mcp_module.db.get_discord_connection = lambda: get_discord_connection(
                self.test_db_path
            )

            try:
                # Test getting history for channel1 (should have 3 messages)
                result = get_history("200000000000000001", last_n_days=30)

                assert "messages" in result
                messages = result["messages"]
                assert len(messages) == 3

                # All messages should be from the same channel
                for message in messages:
                    assert message["channel_id"] == "200000000000000001"

            finally:
                mcp_module.db.get_discord_connection = original_get_connection

    def test_get_user_id_for_name(self):
        """Test fuzzy matching for user/channel names."""
        with get_discord_connection(self.test_db_path) as conn:  # noqa: F841
            # Temporarily patch the db connection
            import discord_mcp.mcp_server as mcp_module

            original_get_connection = mcp_module.db.get_discord_connection
            mcp_module.db.get_discord_connection = lambda: get_discord_connection(
                self.test_db_path
            )

            try:
                # Test exact username match
                result = get_user_id_for_name("testuser1", top_n=3)

                assert "matches" in result
                matches = result["matches"]
                assert len(matches) > 0

                # Should find exact match
                exact_match = None
                for match in matches:
                    if match["name"] == "testuser1":
                        exact_match = match
                        break

                assert exact_match is not None
                assert exact_match["type"] == "user"
                assert exact_match["id"] == "100000000000000001"

                # Test partial channel name match
                result = get_user_id_for_name("gen", top_n=3)
                matches = result["matches"]

                # Should find "general" channel
                general_match = None
                for match in matches:
                    if match["name"] == "general":
                        general_match = match
                        break

                assert general_match is not None
                assert general_match["type"] == "channel"
                assert general_match["id"] == "200000000000000001"

            finally:
                mcp_module.db.get_discord_connection = original_get_connection
