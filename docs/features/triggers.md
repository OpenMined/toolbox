# Triggers

Toolbox triggers allow you to automate tasks in your MCP pipeline. Triggers can run on a schedule or respond to events from MCP servers.

## Types of Triggers

Toolbox supports two types of triggers:

1. **Scheduled Triggers** - Run scripts at specific times using cron expressions
2. **Event-Driven Triggers** - Run scripts in response to events from MCP servers

## Setup

To use triggers, you need to install the toolbox daemon. This will add the toolbox daemon to your launchd, so it will start automatically when you login.

```bash
tb daemon install
```

To uninstall and remove from launchd:

```bash
tb daemon uninstall
```

To see the status of the daemon:

```bash
tb daemon status
```

## Scheduled Triggers

Scheduled triggers run scripts at specific times using cron expressions.

### Creating a Scheduled Trigger

As an example trigger, the toolbox repository contains a script that scrapes trending github repositories that contain 'MCP' keywords. We can register this script to run daily at 12:00 by using the following command:

```bash
tb trigger add \
    --name "github-trending" \
    --script "examples/search_github_trigger.py" \
    --cron "0 12 * * *"
```

### Cron Expressions

The `--cron` parameter accepts standard cron expressions:

- `0 12 * * *` - Daily at 12:00
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1` - Every Monday at 9:00

For more detailed cron syntax and examples, see [crontab.guru](https://crontab.guru/).

## Event-Driven Triggers

Event-driven triggers respond to events sent by MCP servers. Toolbox automatically routes events from MCP servers to registered trigger scripts.

### Example: Slack to Obsidian Workflow

To illustrate how event-driven triggers work, let's create an example workflow that automatically saves Slack mentions to your Obsidian vault.

**Note:** This is just an example, the actual events available from Slack may differ.

#### Step 1: MCP Server Emits Events

The MCP server emits an event when you are mentioned in a Slack message:

```python
# Slack MCP server emits events with message data
from toolbox_events import send_event

send_event(
    name="message.mentioned",
    data={
        "channel": "engineering",
        "author": "Jane Doe",
        "message": "Hey @you, can we review the API design?"
    }
)
```

Each event automatically includes:

- `source` - The name of the MCP server that sent the event
- `timestamp` - The time the event was sent

#### Step 2: Create a Trigger Script

Create a script that receives and processes these events, appending each mention to a markdown file in your Obsidian vault:

```python
# save_slack_to_obsidian.py
from toolbox_events import get_events
from pathlib import Path

OBSIDIAN_VAULT = Path.home() / "ObsidianVault"
MENTIONS_FILE = OBSIDIAN_VAULT / "slack_mentions.md"

events = get_events()

for event in events:
    if event.name == "message.mentioned":
        # Using automatic event.timestamp and custom data fields
        content = (
            f"- [{event.timestamp}] "
            f"**{event.data['author']}**: "
            f"{event.data['message']}\n"
        )
        with open(MENTIONS_FILE, "a") as f:
            f.write(content)
```

!!! note

    `get_events()` returns only unprocessed events that match the trigger's registered event names and sources. Once consumed, events won't be received again in subsequent trigger runs.

#### Step 3: Register the Trigger

Register the trigger to listen for `message.mentioned` events from the Slack MCP server:

```bash
tb trigger add \
    --name "slack-to-obsidian" \
    --script "save_slack_to_obsidian.py" \
    --event "message.mentioned" \
    --event-source "slack-mcp"
```

### Event Filtering Options

When registering event-based triggers, you can control which events to receive:

- **Multiple events/sources**: Provide `--event` and `--event-source` multiple times
- **All sources**: Omit `--event-source` to listen for events from all sources
- **All events from a source**: Omit `--event` to listen for all events from specific sources
- **Schedule-only**: Omit both `--event` and `--event-source` to run only on schedule

Example with multiple events:

```bash
tb trigger add \
    --name "obsidian-processor" \
    --script "process_files.py" \
    --event "file.created" \
    --event "file.modified" \
    --event "file.deleted" \ # (1)!
    --event-source "obsidian-mcp" # (2)!
```

1.  You can specify multiple `--event` flags to listen for multiple event types

2.  You can specify multiple `--event-source` flags to listen to events from multiple MCP servers

## Managing Triggers

### List All Triggers

```bash
tb trigger list
```

### Show Trigger Status

View the status and last 5 executions of a trigger:

```bash
tb trigger show github-trending -n 5
```

### Remove a Trigger

```bash
tb trigger uninstall "github-trending"
```

## API Reference

### Sending Events (MCP Servers)

MCP servers can send events using the `toolbox_events` package:

```python
from toolbox_events import send_event

send_event(
    name="file_processed",
    data={"filename": "document.pdf", "pages": 10}
)
```

### Receiving Events (Trigger Scripts)

Trigger scripts receive events using `get_events()`:

```python
from toolbox_events import get_events

events = get_events()
for event in events:
    print(f"{event.name}: {event.data}")
```
