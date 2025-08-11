# CLAUDE.md - Discord MCP Package

This file provides specific guidance to Claude Code when working with the discord_mcp package.

## Critical Testing Rules

**🚨 NEVER RUN LIVE TESTS WITHOUT EXPLICIT PERMISSION 🚨**

- **ONLY run `pytest` or `just test`** - these run unit tests with mock data
- **NEVER run `pytest -m live` or `just test_live`** unless explicitly asked by the user
- Live tests make actual Discord API calls and should only be run when specifically requested
- Unit tests use MockDiscordClient with test fixtures and are safe to run anytime

## Testing Commands

### Safe Commands (Always OK to run):
```bash
pytest                    # Unit tests only (default)
just test                # Unit tests only  
pytest tests/test_unit_api.py  # Unit tests only
```

### Restricted Commands (Only when explicitly requested):
```bash
pytest -m live          # Live Discord API tests - DO NOT RUN
just test_live          # Live Discord API tests - DO NOT RUN  
```

## Project Structure

### Core Components
- **DiscordClient**: Real Discord API client using httpx
- **MockDiscordClient**: Test client that inherits from DiscordClient but mocks HTTP calls
- **API Functions**: download_messages, download_channels, download_guilds

### Test Structure
- **Unit Tests** (`tests/test_unit_api.py`): Use MockDiscordClient with test fixtures
- **Live Tests** (`tests/test_live_api.py`): Use real DiscordClient with Discord API
- **Test Assets** (`discord_mcp/test_assets/`): JSON fixtures with real Discord data

### Key Architecture
- MockDiscordClient inherits from DiscordClient and only overrides `_make_request()`
- This ensures unit tests use the same business logic as production
- Test data comes from real Discord exports stored in test_assets/

## Development Guidelines

- Always prefer editing existing files over creating new ones
- Use the existing test patterns when adding new functionality
- MockDiscordClient automatically supports new DiscordClient methods
- Unit tests should assert non-empty data to ensure mock is working

## Environment
- Requires `DISCORD_TOKEN` environment variable for live tests only. The token is expected to be present during development
- Unit tests work without any environment setup