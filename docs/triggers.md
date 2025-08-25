# Triggers

Toolbox can run scripts defined by you on a schedule. This is useful for automating tasks as part of your MCP pipeline.

## Setup

First, to be able to run triggers, you need to install the toolbox daemon. This will add the toolbox daemon to your launchd, so it will start automatically when you login.

```
tb daemon install
```

To uninstall and remove from launchd:

```
tb daemon uninstall
```

To see the status of the daemon:

```
tb daemon status
```

## Creating Triggers

As example, we have provided a script to search github for repositories with the keyword "MCP".

```
# Run `search_github_trigger.py` daily at 12:00
tb trigger add --name "github-trending" --script "examples/search_github_trigger.py" --cron "0 12 * * *"
```

## Managing Triggers

To uninstall a trigger:

```
tb trigger uninstall "github-trending"
```

To show all triggers:

```
tb trigger list
```

To show the status and last 5 executions of a trigger:

```
tb trigger show github-trending -n 5
```

## Cron Expressions

The `--cron` parameter accepts standard cron expressions to schedule triggers at a specific time or interval. For example:

- `0 12 * * *` - Daily at 12:00
- `0 */6 * * *` - Every 6 hours
- `0 9 * * 1` - Every Monday at 9:00

For more detailed cron syntax and examples, see [crontab.guru](https://crontab.guru/) - an interactive cron expression editor and reference.

## Event-Driven Triggers

Triggers can respond to events sent by MCP servers. Toolbox automatically configures the environment so events are routed correctly.

### Sending Events from MCP Servers

Toolbox receives events from all MCP servers launched by Toolbox. Use the `toolbox_events` package to send events to the daemon:

```python
from toolbox_events import send_event

# Send an event when something happens
send_event(
    name="file_processed",
    data={"filename": "document.pdf", "pages": 10}
)
```

Each event automatically includes:

- `source` - The name of the MCP server that sent the event
- `timestamp` - The time the event was sent

### Receiving Events in Trigger Scripts

Toolbox automatically sends events to trigger scripts that are registered to listen for them. Scripts receive all matching events:

```python
from toolbox_events import get_events

# Get all events for this trigger
events = get_events()

for event in events:
    print(f"{event.name}: {event.data}")
```

### Creating Event-Based Triggers

Use the `trigger add` command to create triggers that respond to specific events.

Example: Create a trigger that responds to file events from the `obsidian-mcp` server:

```bash
tb trigger add \
    --name "obsidian-event-processor" \
    --script "/path/to/your/script.py" \
    --event "file.created" \
    --event "file.updated" \
    --event "file.deleted" \
    --event-source "obsidian-mcp"
```

#### Event Filtering

- **Multiple events/sources**: Provide `--event` and `--event-source` multiple times to listen for multiple events from multiple sources
- **All sources**: Omit `--event-source` to listen for events from all sources
- **All events from a source**: Omit `--event` to listen for all events from specific sources
- **Schedule-only**: Omit both `--event` and `--event-source` to run only on schedule without listening for events
