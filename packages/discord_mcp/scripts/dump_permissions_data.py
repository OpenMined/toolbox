#!/usr/bin/env python3
"""
Script to dump all API call results needed for permission computation testing.
This creates JSON files that can be used for unit tests without making live API calls.
"""

import json
import os
import sys
from pathlib import Path

# Add the package root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_mcp.client import DiscordClient


def dump_permissions_data():
    """Dump all API data needed for permission computation."""
    # Check if DISCORD_TOKEN is set
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Error: DISCORD_TOKEN environment variable is required")
        sys.exit(1)
    
    print("🗂️  Dumping Discord Permissions API Data")
    print("=" * 45)
    
    output_dir = Path("/tmp")
    
    try:
        client = DiscordClient(token)
        
        # Find Claude Developers guild
        print("🔍 Finding Claude Developers guild...")
        claude_guild = None
        user_guilds = list(client.get_user_guilds())
        
        for guild in user_guilds:
            if guild["name"] == "Claude Developers":
                claude_guild = guild
                break
        
        if not claude_guild:
            print("❌ Claude Developers guild not found")
            sys.exit(1)
        
        guild_id = claude_guild["id"]
        print(f"✅ Found: {claude_guild['name']} ({guild_id})")
        
        # 1. Dump user guilds
        print("\n📊 Dumping user guilds...")
        guilds_file = output_dir / "permissions_user_guilds.json"
        with open(guilds_file, 'w') as f:
            json.dump(user_guilds, f, indent=2)
        print(f"   → {guilds_file}")
        
        # 2. Dump current user
        print("\n👤 Dumping current user...")
        current_user = client.get_current_user()
        user_file = output_dir / "permissions_current_user.json"
        with open(user_file, 'w') as f:
            json.dump(current_user, f, indent=2)
        print(f"   → {user_file}")
        
        user_id = current_user["id"]
        
        # 3. Dump member roles
        print(f"\n🎭 Dumping member roles for user {user_id}...")
        member_roles = client.get_member_roles(guild_id, user_id)
        roles_file = output_dir / "permissions_member_roles.json"
        with open(roles_file, 'w') as f:
            json.dump(member_roles, f, indent=2)
        print(f"   → {roles_file}")
        print(f"   Found {len(member_roles)} roles")
        
        # 4. Dump guild roles
        print(f"\n📝 Dumping guild roles...")
        guild_roles_dict = client.get_guild_roles(guild_id)
        guild_roles_file = output_dir / "permissions_guild_roles.json"
        with open(guild_roles_file, 'w') as f:
            json.dump(guild_roles_dict, f, indent=2)
        print(f"   → {guild_roles_file}")
        print(f"   Found {len(guild_roles_dict)} total roles")
        
        # 5. Dump guild channels with permission overwrites
        print(f"\n📺 Dumping guild channels with permission overwrites...")
        channels = list(client.get_guild_channels(guild_id))
        channels_file = output_dir / "permissions_guild_channels.json"
        with open(channels_file, 'w') as f:
            json.dump(channels, f, indent=2)
        print(f"   → {channels_file}")
        print(f"   Found {len(channels)} channels")
        
        # 6. Dump guild info
        print(f"\n🏰 Dumping guild info...")
        guild_info = client.get_guild(guild_id)
        guild_file = output_dir / "permissions_guild_info.json"
        with open(guild_file, 'w') as f:
            json.dump(guild_info, f, indent=2)
        print(f"   → {guild_file}")
        
        # Summary
        print(f"\n🎉 Data dump complete!")
        print("=" * 45)
        print(f"Files created in {output_dir}:")
        print(f"  • permissions_user_guilds.json ({len(user_guilds)} guilds)")
        print(f"  • permissions_current_user.json (user: {current_user['username']})")
        print(f"  • permissions_member_roles.json ({len(member_roles)} roles)")
        print(f"  • permissions_guild_roles.json ({len(guild_roles_dict)} roles)")
        print(f"  • permissions_guild_channels.json ({len(channels)} channels)")
        print(f"  • permissions_guild_info.json (guild: {guild_info['name']})")
        
        # Show which channels should be accessible for verification
        from discord_mcp.permissions_api import compute_channel_permissions
        print(f"\n✅ Expected accessible channels (for test verification):")
        accessible_results = compute_channel_permissions(guild_id, client)
        accessible_channels = [
            next((c.get("name", f"Channel-{channel_id}") for c in channels if c["id"] == channel_id), f"Channel-{channel_id}")
            for channel_id, has_access in accessible_results.items() if has_access
        ]
        for i, channel_name in enumerate(sorted(accessible_channels), 1):
            print(f"  {i:2d}. #{channel_name}")
        print(f"\nTotal: {len(accessible_channels)} accessible channels")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    dump_permissions_data()