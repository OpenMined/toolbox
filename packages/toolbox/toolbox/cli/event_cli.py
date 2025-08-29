import json
import textwrap
from datetime import datetime, timezone

import typer
from tabulate import tabulate

from toolbox.analytics import track_cli_command
from toolbox.triggers.trigger_store import get_db

app = typer.Typer(no_args_is_help=True)


@app.command()
@track_cli_command("event add")
def add(
    name: str = typer.Option(..., "--name", "-n", help="Name of the event"),
    source: str = typer.Option(..., "--source", "-s", help="Source of the event"),
    data: str = typer.Option("{}", "--data", "-d", help="Event data as JSON string"),
):
    """Add a single event to the trigger database"""
    db = get_db()

    # Parse the data JSON
    try:
        event_data = json.loads(data)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON data: {e}", err=True)
        raise typer.Exit(1)

    # Create the event
    event_dict = {
        "name": name,
        "source": source,
        "data": event_data,
        "timestamp": datetime.now(timezone.utc),
    }

    try:
        db.events.create_many([event_dict])
        typer.echo(f"✓ Added event '{name}' from source '{source}'")
    except Exception as e:
        typer.echo(f"Error adding event: {e}", err=True)
        raise typer.Exit(1)


@app.command()
@track_cli_command("event list")
def list(
    source: str | None = typer.Option(
        None, "--source", "-s", help="Source of the event"
    ),
    event_name: str | None = typer.Option(
        None, "--event-name", "-e", help="Name of the event"
    ),
    limit: int = typer.Option(
        10, "--limit", "-n", help="Limit the number of events to show"
    ),
    offset: int = typer.Option(
        0, "--offset", "-o", help="Offset the number of events to show"
    ),
):
    """List all events"""
    db = get_db()

    events = db.events.get_all(
        source=source, name=event_name, limit=limit, offset=offset
    )

    # make table
    col_names = ["name", "source", "timestamp", "data"]

    table_data = []
    for event in events:
        data_truncated = textwrap.shorten(json.dumps(event.data), width=128)
        table_data.append(
            [
                event.name,
                event.source,
                event.timestamp,
                data_truncated,
            ]
        )

    print(tabulate(table_data, headers=col_names))
