# Notifications

Toolbox provides a simple way to send notifications from your trigger scripts and MCP servers using [ntfy.sh](https://ntfy.sh/).

## Setup

Your default notification topic is automatically configured during `tb setup`. To view or change it:

```bash
# View current default notification topic
tb settings

# Set a new default topic
tb set-notification-topic <topic>
```

To receive notifications on your phone:

1. Install the [ntfy.sh app](https://ntfy.sh/docs/subscribe/phone/)
2. Subscribe to your topic (e.g., `tb-username-a3f2`)

## Sending Notifications

### From Trigger Scripts

Use the `notify` function from `toolbox_events` to send notifications:

```python
from toolbox_events import notify

# Simple notification (uses default topic)
notify("Task completed successfully")

# With title and priority
notify(
    message="10 new repositories found matching 'MCP'",
    title="GitHub Search Results",
    priority=4  # 1=min, 2=low, 3=default, 4=high, 5=urgent
)

# With custom topic and tags
notify(
    message="Server backup completed",
    title="Backup Status",
    tags=["backup", "success"],
    topic="server-alerts"
)
```

## Priority Levels

Notifications support 5 priority levels:

- `1` - Minimum priority
- `2` - Low priority
- `3` - Default priority (default)
- `4` - High priority
- `5` - Urgent priority

## Configuration

The notification system can be configured via environment variables:

```bash
# Use custom ntfy server (default: https://ntfy.sh)
export TOOLBOX_NOTIFIER_SERVER_URL=https://your-ntfy-server.com

# Set default topic
export TOOLBOX_NOTIFIER_DEFAULT_TOPIC=my-notifications
```

## Example: Notification in Event-Driven Trigger

```python
from toolbox_events import get_events, notify

# Process events and notify on important ones
events = get_events()

important_count = 0
for event in events:
    if event.name == "critical.error":
        important_count += 1

if important_count > 0:
    notify(
        f"⚠️ {important_count} errors detected",
        title="System Alert",
        priority=4,
        tags=["error", "alert"]
    )
```
