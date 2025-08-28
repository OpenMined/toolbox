# Quick Start

This guide will get you up and running with Toolbox in minutes.

## First Steps

### 1. Verify Installation

After [installing Toolbox](installation.md), verify it's working:

```bash
tb info
```

### 2. Initial Setup

Run the setup command to configure Toolbox:

```bash
tb setup
```

This will:

- Configure your notification settings
- Set up analytics preferences
- Create necessary directories

## Basic Commands

### Browse Available MCP Servers

See what's available to install:

```bash
tb list-store
```

### Install Your First MCP Server

Let's start with a popular one - Slack:

```bash
tb install slack-mcp
```

Follow the prompts to:

1. Authenticate with Slack
2. Configure which workspaces to monitor
3. Set up any background agents

### List Installed Apps

View all your installed MCP servers:

```bash
tb list
```

### Check App Details

Get detailed information about an installed app:

```bash
tb show slack-mcp
```

### View Logs

Monitor what your MCP server is doing:

```bash
# View recent logs
tb log slack-mcp

# Follow logs in real-time
tb log slack-mcp -f
```

## Using with Claude

Once you've installed an MCP server, it's automatically available in Claude Desktop:

1. Open Claude Desktop
2. Start a new conversation
3. Your MCP servers will be available as tools Claude can use
4. Try asking: "Show me my recent Slack messages"

## What's Next?

- Learn about [Triggers](../features/triggers.md) to automate tasks
- Set up [Notifications](../features/notifications.md) for important events
- Browse available MCP servers with `tb list-store`
- Check out [Use Cases](../use-cases/slack.md) for inspiration

## Getting Help

- Run `tb --help` for command documentation
- Report issues at [GitHub Issues](https://github.com/OpenMined/toolbox/issues)
- Join our community discussions
