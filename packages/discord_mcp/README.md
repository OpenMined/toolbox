# Discord Downloader

A Python package for downloading Discord messages, users, and channel data using the Discord REST API with proper rate limiting and retry logic.

## Features

- **Rate Limiting**: Respects Discord's rate limits with configurable preferences
- **Retry Logic**: Exponential backoff with up to 8 retry attempts
- **Token Auto-Detection**: Automatically detects user vs bot tokens
- **JSON Output**: Saves data to structured JSON files in `/tmp`
- **Environment Variables**: Configuration via environment variables

## Installation

```bash
pip install aiohttp
```

## Usage

### Environment Variables

Set these environment variables before running the scripts:

```bash
export DISCORD_TOKEN="your_discord_token_here"
export DISCORD_GUILD_NAME="Your Server Name"
export DISCORD_CHANNEL_NAME="channel-name"  # Only for messages
export OUTPUT_DIR="/tmp"  # Optional, defaults to /tmp
export DAYS_BACK="365"  # Optional, defaults to 365 (1 year)
```

### Download Messages

```bash
python -m discord_downloader.download_messages
```

Downloads all messages from the specified channel in the last year (configurable via `DAYS_BACK`).

### Download Users

```bash
python -m discord_downloader.download_users
```

Downloads user information from the server by sampling recent messages across all accessible channels.

### Download Channels

```bash
python -m discord_downloader.download_channels
```

Downloads channel information and structure from the server.

## Programmatic Usage

```python
import asyncio
from discord_downloader import DiscordClient, download_messages

async def example():
    # Using the client directly
    async with DiscordClient("your_token") as client:
        user = await client.get_current_user()
        print(f"Authenticated as: {user['username']}")
    
    # Using the API functions
    output_path = await download_messages(
        token="your_token",
        guild_name="My Server",
        channel_name="general",
        output_dir="/tmp",
        days_back=365
    )
    print(f"Messages saved to: {output_path}")

asyncio.run(example())
```

## Rate Limiting

The client implements the same rate limiting strategy as the original DiscordChatExporter:

- **Respects Discord's advisory rate limits** (X-RateLimit-Remaining, X-RateLimit-Reset-After)
- **Automatic delays** when approaching rate limits
- **429 response handling** with Retry-After header support
- **Exponential backoff** for network errors

## Output Format

All data is saved as JSON files with metadata:

### Messages
```json
{
  "metadata": {
    "guild": {...},
    "channel": {...},
    "export_date": "2024-01-01T00:00:00Z",
    "message_count": 1500,
    "date_range": {
      "since": "2023-01-01T00:00:00Z",
      "until": "2024-01-01T00:00:00Z"
    }
  },
  "messages": [...]
}
```

### Users
```json
{
  "metadata": {
    "guild": {...},
    "export_date": "2024-01-01T00:00:00Z",
    "user_count": 250,
    "current_user": {...}
  },
  "users": [...]
}
```

### Channels
```json
{
  "metadata": {
    "guild": {...},
    "export_date": "2024-01-01T00:00:00Z",
    "channel_count": 15
  },
  "channels": [...]
}
```

## Security Notes

- **User tokens**: Using user tokens for automation violates Discord's Terms of Service
- **Bot tokens**: Recommended for automated use, requires Message Content Intent for message content
- **Token storage**: Never commit tokens to version control
- **Rate limiting**: Always respect Discord's rate limits to avoid account suspension

## Error Handling

The client handles various Discord API errors:

- **401 Unauthorized**: Invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limited (automatic retry)
- **5xx Server Errors**: Discord server issues (automatic retry)