#!/usr/bin/env python3
"""Script to download channels and save to JSON file."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discord_mcp.api import download_channels


def main():
    """Download channels and save to /tmp."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        # Download channels
        result = download_channels(token=token, guild_name="Claude Developers")

        # Save to file
        output_path = "/tmp/channels_test_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Channels saved to: {output_path}")
        print(f"Channel count: {result['metadata']['channel_count']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
