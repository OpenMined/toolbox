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
