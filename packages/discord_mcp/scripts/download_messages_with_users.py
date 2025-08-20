#!/usr/bin/env python3
"""Script to download messages with users and save to JSON file."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_mcp.api import download_messages_with_users


def main():
    """Download messages with users and save to /tmp."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Download messages with users
        result = download_messages_with_users(
            token=token,
            guild_name="Claude Developers",
            channel_name="general",
            days_back=1
        )
        
        # Save to file
        output_path = "/tmp/messages_with_users_test_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Messages with users saved to: {output_path}")
        print(f"Message count: {result['metadata']['message_count']}")
        print(f"User count: {result['metadata']['user_count']}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()