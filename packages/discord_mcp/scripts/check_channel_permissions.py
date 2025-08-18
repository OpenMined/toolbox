#!/usr/bin/env python3
"""
Script to analyze Discord channel permissions and determine which channels you have access to
without making individual API calls for each channel.

This script examines channel permission overwrites and your roles to compute effective permissions.
"""

import os
import sys
import time
from pathlib import Path

# Add the package root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_mcp.client import DiscordClient
from discord_mcp.permissions_api import compute_channel_permissions


def main():
    """Main script function."""
    # Check if DISCORD_TOKEN is set
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Error: DISCORD_TOKEN environment variable is required")
        print("Set it with: export DISCORD_TOKEN='your_discord_token'")
        sys.exit(1)

    print("🔍 Discord Channel Permission Analyzer")
    print("=====================================")

    # Start timing
    start_time = time.time()

    try:
        client = DiscordClient(token)

        # Find Claude Developers guild only
        claude_guild = None
        for guild in client.get_user_guilds():
            if guild["name"] == "Claude Developers":
                claude_guild = guild
                break

        if not claude_guild:
            print("❌ Claude Developers guild not found")
            sys.exit(1)

        guild_id = claude_guild["id"]
        guild_name = claude_guild["name"]
        print(f"📊 Analyzing only: {guild_name}")

        all_results = {}

        print(f"\n🏰 Analyzing: {guild_name} ({guild_id})")

        try:
            guild_results = compute_channel_permissions(guild_id, client)
            all_results[guild_id] = {"name": guild_name, "channels": guild_results}

            # Summary for this guild
            accessible = sum(1 for has_access in guild_results.values() if has_access)
            total = len(guild_results)
            print(f"  📊 Summary: {accessible}/{total} channels accessible")

        except Exception as e:
            print(f"  ❌ Error analyzing guild {guild_name}: {e}")
            sys.exit(1)

        # Overall summary
        print("\n🎉 Analysis Complete!")
        print("=" * 50)

        total_accessible = 0
        total_channels = 0

        for guild_id, data in all_results.items():
            accessible = sum(
                1 for has_access in data["channels"].values() if has_access
            )
            total = len(data["channels"])
            total_accessible += accessible
            total_channels += total
            print(f"  {data['name']}: {accessible}/{total} accessible")

        print(f"\n📈 Overall: {total_accessible}/{total_channels} channels accessible")

        # Show ACCESSIBLE channels with names
        print("\n✅ ACCESSIBLE CHANNELS:")
        for guild_id, data in all_results.items():
            accessible_channels = []
            channels = list(client.get_guild_channels(guild_id))
            channel_map = {
                c["id"]: c.get("name", f"Channel-{c['id']}") for c in channels
            }

            for channel_id, has_access in data["channels"].items():
                if has_access:
                    channel_name = channel_map.get(channel_id, f"Channel-{channel_id}")
                    accessible_channels.append(f"#{channel_name}")

            if accessible_channels:
                print(f"  {data['name']}:")
                for channel in sorted(accessible_channels):
                    print(f"    • {channel}")
            else:
                print(f"  {data['name']}: No accessible channels")

        # Show inaccessible channels
        print("\n🚫 INACCESSIBLE CHANNELS:")
        for guild_id, data in all_results.items():
            inaccessible_channels = []
            channels = list(client.get_guild_channels(guild_id))
            channel_map = {
                c["id"]: c.get("name", f"Channel-{c['id']}") for c in channels
            }

            for channel_id, has_access in data["channels"].items():
                if not has_access:
                    channel_name = channel_map.get(channel_id, f"Channel-{channel_id}")
                    inaccessible_channels.append(f"#{channel_name}")

            if inaccessible_channels:
                print(f"  {data['name']}: {len(inaccessible_channels)} channels")
                for channel in sorted(inaccessible_channels)[:5]:  # Show first 5
                    print(f"    • {channel}")
                if len(inaccessible_channels) > 5:
                    print(f"    ... and {len(inaccessible_channels) - 5} more")
            else:
                print(f"  {data['name']}: All channels accessible!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        if "client" in locals():
            client.close()

        # Show timing
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n⏱️  Total execution time: {duration:.2f} seconds")


if __name__ == "__main__":
    main()
