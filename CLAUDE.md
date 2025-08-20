# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a privacy-first toolbox for installing local and remote MCP (Model Context Protocol) servers for personal data. The project is structured as a uv workspace with three main packages:

- **toolbox**: Core CLI application for managing MCP server installations
- **notes_mcp**: MCP server for meeting notes and audio transcription
- **syftbox_queryengine**: Query engine for SyftBox integration

## Development Commands

### Installation and Setup

```bash
# Install the project in development mode
uv pip install -e .
```

### Running the CLI

```bash
# Using the main toolbox command
tb --help

# List installed MCP apps
tb list

# Install a new MCP app
tb install <app_name>

# Show details of an MCP app
tb show <app_name>
```

### Package-specific Commands

Each package can be developed independently:

```bash
# Work on specific packages
cd packages/toolbox
cd packages/notes_mcp
cd packages/syftbox_queryengine
```

## Architecture

### Workspace Structure

- **Root**: Contains the main project configuration and workspace setup
- **packages/toolbox**: CLI application built with Typer for MCP server management
- **packages/notes_mcp**: FastAPI-based MCP server for meeting notes with audio transcription
- **packages/syftbox_queryengine**: FastAPI server for SyftBox integration

### Key Components

#### Toolbox CLI (packages/toolbox/)

- Entry point: `toolbox/cli/cli.py:app`
- Main commands: install, list, show
- Database: SQLite for tracking installed MCPs
- Store system: JSON-based MCP definitions with installation callbacks

#### Notes MCP (packages/notes_mcp/)

- MCP server: `notes_mcp/mcp_server.py`
- FastAPI server: `notes_mcp/fastapi_server.py`
- Background workers for audio transcription and meeting indexing
- Uses Anthropic API for content processing

#### SyftBox Query Engine (packages/syftbox_queryengine/)

- FastAPI server for SyftBox RPC communication
- Authentication and sync functionality
- Integration with fastsyftbox library

### Data Flow

1. Meeting notes MCP processes audio files and generates transcriptions
2. Background workers index meetings and extract todos
3. CLI toolbox manages installation and configuration of MCP servers

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Required for notes MCP functionality

### Python Version

- Requires Python ≥3.12
- All packages use modern Python features and type hints

### Dependencies

- **FastAPI/Uvicorn**: Web frameworks for MCP servers
- **Typer**: CLI framework for toolbox
- **MCP**: Model Context Protocol implementation
- **Anthropic**: AI API integration
- **SQLite**: Local database storage

## Startup Sequence

### Initialization Process

- You can first start the syftbox_queryengine, and then start the notes_mcp
- The Syftboxquery engine will register an account with the NoteMCP server
- The NoteMCP server will then start polling the Syftbox query engine for new data and indexed data
