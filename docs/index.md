!!! warning "Beta Documentation"
These docs are in beta and subject to change. Please refer to the [README.md](https://github.com/OpenMined/toolbox/blob/main/README.md) for the latest information.

# Toolbox

[![PyPI version](https://badge.fury.io/py/syft-toolbox.svg)](https://badge.fury.io/py/syft-toolbox)
[![Python](https://img.shields.io/pypi/pyversions/syft-toolbox)](https://pypi.org/project/syft-toolbox/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/OpenMined/toolbox/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/OpenMined/toolbox?style=social)](https://github.com/OpenMined/toolbox)

A privacy-first tool to install MCP servers and background agents for your personal data.

<!-- <div style="position: relative; padding-bottom: 64.92335437330928%; height: 0;"><iframe src="https://www.loom.com/embed/8c85f602fe4c47a5b8b8ddc827d4a048?sid=6c3f7861-1e74-43dd-a296-23e2f546a933" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div> -->

## Overview

Toolbox is a CLI tool for installing and managing [MCP](https://github.com/modelcontextprotocol/python-sdk) servers and background agents, **made for developers**.

- Install **MCP servers** with **background agents** using `tb install <appname>`
- Support for popular developer tools (GitHub, Slack, Discord, Obsidian, Gmail, etc.)
- Compatible with multiple clients (Claude Desktop, Cursor)
- Choose between fully local or free hosted options

## Quick Start

### Installation

```bash
# Install via uv
uv tool install --prerelease allow --python 3.12 -U syft-toolbox

# Verify installation
tb info
```

### Basic Commands

```bash
# List available apps
tb list-store

# Install an app
tb install slack-mcp

# List installed apps
tb list

# Show app details
tb show <appname>
```

## Features

### [Triggers](features/triggers.md)

Automate tasks with scheduled scripts and event-driven workflows.

### [Notifications](features/notifications.md)

Send notifications from your triggers and MCP servers using ntfy.sh.

## Available MCP Servers

| Name                 | Description                 | Install                           |
| -------------------- | --------------------------- | --------------------------------- |
| slack-mcp            | Access Slack messages       | `tb install slack-mcp`            |
| discord-mcp          | Access Discord messages     | `tb install discord-mcp`          |
| obsidian-mcp         | Manage Obsidian notes       | `tb install obsidian-mcp`         |
| github-mcp           | Manage GitHub issues & PRs  | `tb install github-mcp`           |
| whatsapp-desktop-mcp | Access WhatsApp messages    | `tb install whatsapp-desktop-mcp` |
| pdf-mcp              | Process local documents     | `tb install pdf-mcp`              |
| meeting-notes-mcp    | Transcribe audio recordings | `tb install meeting-notes-mcp`    |

## Links

- [GitHub Repository](https://github.com/OpenMined/toolbox)
- [PyPI Package](https://pypi.org/project/syft-toolbox/)
