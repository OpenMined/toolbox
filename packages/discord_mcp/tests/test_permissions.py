"""Unit tests for Discord permission computation functionality."""

import pytest

from discord_mcp.permissions_api import compute_channel_permissions
from tests.mock_client import MockDiscordClient


class TestPermissions:
    """Test Discord permission computation functionality."""
    
    def test_permission_computation_with_mock_client(self):
        """Test that permission computation works correctly with mock client data."""
        # Create mock client that will use our dumped permission test data
        client = MockDiscordClient("test_token", use_permissions_data=True)
        
        # The guild ID from our test data (Claude Developers)
        claude_developers_guild_id = "1072196207201501266"
        
        # Compute permissions using the mock client
        results = compute_channel_permissions(claude_developers_guild_id, client)
        
        # Verify we got results
        assert isinstance(results, dict), "Should return a dictionary of channel_id -> bool"
        assert len(results) > 0, "Should have at least some channel results"
        
        # Count accessible channels
        accessible_channels = [channel_id for channel_id, has_access in results.items() if has_access]
        inaccessible_channels = [channel_id for channel_id, has_access in results.items() if not has_access]
        
        print(f"\n📊 Permission computation results:")
        print(f"  Total channels: {len(results)}")
        print(f"  Accessible: {len(accessible_channels)}")
        print(f"  Inaccessible: {len(inaccessible_channels)}")
        
        # Verify we have the expected number of accessible channels
        # Based on our live test, we should have exactly 12 accessible channels
        assert len(accessible_channels) == 12, f"Expected 12 accessible channels, got {len(accessible_channels)}"
        
        # Verify we have some inaccessible channels too
        assert len(inaccessible_channels) > 0, "Should have some inaccessible channels"
        
        # Verify total channels match what we expect (47 text channels from dump)
        assert len(results) == 47, f"Expected 47 total text channels, got {len(results)}"
        
    def test_accessible_channel_names(self):
        """Test that the specific channels we expect to be accessible are accessible."""
        client = MockDiscordClient("test_token", use_permissions_data=True)
        claude_developers_guild_id = "1072196207201501266"
        
        # Get permission results
        results = compute_channel_permissions(claude_developers_guild_id, client)
        
        # Get channel name mapping from mock data
        channels = list(client.get_guild_channels(claude_developers_guild_id))
        channel_names = {c["id"]: c.get("name", f"Channel-{c['id']}") for c in channels}
        
        # Get accessible channel names
        accessible_channel_names = [
            channel_names[channel_id] 
            for channel_id, has_access in results.items() 
            if has_access
        ]
        
        # Expected accessible channels based on our live test
        expected_accessible = {
            "welcome", "📢-announcements", "📅-events", "📰-updates", 
            "🚥-claude-status", "👋-introduce-yourself", "general", 
            "claude-code", "api", "mcp", "off-topic", "🇯🇵-日本語"
        }
        
        print(f"\n✅ Accessible channels: {sorted(accessible_channel_names)}")
        
        # Verify each expected channel is accessible
        for expected_channel in expected_accessible:
            assert expected_channel in accessible_channel_names, f"Expected {expected_channel} to be accessible"
        
        # Verify we don't have unexpected accessible channels
        unexpected_accessible = set(accessible_channel_names) - expected_accessible
        assert len(unexpected_accessible) == 0, f"Unexpected accessible channels: {unexpected_accessible}"
        
    def test_permission_computation_consistency(self):
        """Test that permission computation is consistent across multiple runs."""
        client = MockDiscordClient("test_token", use_permissions_data=True)
        claude_developers_guild_id = "1072196207201501266"
        
        # Run permission computation multiple times
        results1 = compute_channel_permissions(claude_developers_guild_id, client)
        results2 = compute_channel_permissions(claude_developers_guild_id, client)
        
        # Results should be identical
        assert results1 == results2, "Permission computation should be deterministic"
        
        # Verify both have the expected number of accessible channels
        accessible1 = sum(1 for has_access in results1.values() if has_access)
        accessible2 = sum(1 for has_access in results2.values() if has_access)
        
        assert accessible1 == accessible2 == 12, f"Both runs should have 12 accessible channels"
        
    def test_mock_client_permission_methods(self):
        """Test that MockDiscordClient properly supports permission-related methods."""
        client = MockDiscordClient("test_token", use_permissions_data=True)
        
        # Test get_current_user
        user = client.get_current_user()
        assert "id" in user, "Should return user with ID"
        assert "username" in user, "Should return user with username"
        
        # Test get_user_guilds
        guilds = list(client.get_user_guilds())
        assert len(guilds) > 0, "Should return at least one guild"
        
        # Find Claude Developers guild
        claude_guild = None
        for guild in guilds:
            if guild["name"] == "Claude Developers":
                claude_guild = guild
                break
        
        assert claude_guild is not None, "Should find Claude Developers guild"
        guild_id = claude_guild["id"]
        user_id = user["id"]
        
        # Test get_member_roles
        member_roles = client.get_member_roles(guild_id, user_id)
        assert isinstance(member_roles, list), "Should return list of role IDs"
        assert len(member_roles) == 3, "Should have 3 roles based on dumped data"
        
        # Test get_guild_roles
        guild_roles = client.get_guild_roles(guild_id)
        assert isinstance(guild_roles, dict), "Should return dict of role_id -> role_data"
        assert len(guild_roles) == 35, "Should have 35 total roles based on dumped data"
        
        # Test get_guild_channels
        channels = list(client.get_guild_channels(guild_id))
        assert len(channels) > 0, "Should return channels"
        assert len(channels) == 63, "Should have 63 total channels based on dumped data"
        
        # Verify channels have permission_overwrites
        channels_with_overwrites = [c for c in channels if c.get("permission_overwrites")]
        assert len(channels_with_overwrites) > 0, "Should have channels with permission overwrites"


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestPermissions()
    test_instance.test_permission_computation_with_mock_client()
    test_instance.test_accessible_channel_names()
    test_instance.test_permission_computation_consistency()
    test_instance.test_mock_client_permission_methods()
    print("✅ All tests passed!")