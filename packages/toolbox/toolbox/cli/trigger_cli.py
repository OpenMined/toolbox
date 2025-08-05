from pathlib import Path

import typer
from sqlalchemy.exc import IntegrityError

from toolbox.triggers.trigger_store import get_db

app = typer.Typer(no_args_is_help=True)


@app.command()
def add(
    name: str = typer.Option(..., "--name", "-n", help="Name of the trigger"),
    cron_schedule: str = typer.Option(
        ..., "--cron", "-c", help="Cron schedule (e.g., '0 * * * *')"
    ),
    script_path: str = typer.Option(
        ..., "--script", "-s", help="Path to the Python script to execute"
    ),
):
    """Add a new trigger"""
    db = get_db()

    # Verify script path exists
    path = Path(script_path)
    if not path.exists():
        typer.echo(f"Error: Script path '{script_path}' does not exist", err=True)
        raise typer.Exit(1)

    if not path.is_file():
        typer.echo(f"Error: '{script_path}' is not a file", err=True)
        raise typer.Exit(1)

    try:
        # Validate cron schedule
        db.triggers.validate_cron_schedule(cron_schedule)

        # Create trigger
        trigger = db.triggers.create(name, cron_schedule, path.absolute())
        typer.echo(f"✓ Added trigger '{trigger.name}'")

    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except IntegrityError:
        typer.echo(f"Error: Trigger '{name}' already exists", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error creating trigger: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def list():
    """List all triggers"""
    from tabulate import tabulate

    db = get_db()
    triggers = db.triggers.get_all()

    if not triggers:
        typer.echo("No triggers found")
        return

    # Prepare data for tabulate
    table_data = []
    for trigger in triggers:
        status = "✓ enabled" if trigger.enabled else "✗ disabled"
        table_data.append(
            [
                trigger.name,
                status,
                trigger.cron_schedule,
                trigger.script_path,
                trigger.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    print(
        tabulate(
            table_data,
            headers=["Name", "Status", "Schedule", "Script", "Created"],
            tablefmt="grid",
        )
    )


@app.command()
def show(
    name: str = typer.Argument(..., help="Name of the trigger to show"),
):
    """Show a trigger"""
    db = get_db()
    trigger = db.triggers.get_by_name(name)

    if not trigger:
        typer.echo(f"Error: Trigger '{name}' not found", err=True)
        raise typer.Exit(1)

    status = "enabled" if trigger.enabled else "disabled"
    typer.echo(f"Trigger: {trigger.name}")
    typer.echo(f"  ID: {trigger.id}")
    typer.echo(f"  Status: {status}")
    typer.echo(f"  Schedule: {trigger.cron_schedule}")
    typer.echo(f"  Script: {trigger.script_path}")
    typer.echo(f"  Created: {trigger.created_at}")

    # Show recent executions
    executions = db.executions.get_all(trigger_id=trigger.id, limit=5)
    if executions:
        typer.echo("\nRecent executions:")
        for ex in executions:
            if ex.completed_at:
                status = "✓" if ex.exit_code == 0 else "✗"
                typer.echo(f"  {status} {ex.completed_at} (exit: {ex.exit_code})")
                # print tail of logs (ex.logs)
                last_log_lines = "\n".join(ex.logs.split("\n")[-10:])
                typer.echo(f"\n  Logs: {last_log_lines}")
            else:
                typer.echo(f"  ⏳ {ex.created_at} (running)")
    else:
        typer.echo("\nNo executions found")


@app.command()
def enable(
    name: str = typer.Argument(..., help="Name of the trigger to enable"),
):
    """Enable a trigger"""
    db = get_db()
    trigger = db.triggers.get_by_name(name)

    if not trigger:
        typer.echo(f"Error: Trigger '{name}' not found", err=True)
        raise typer.Exit(1)

    if trigger.enabled:
        typer.echo(f"Trigger '{name}' is already enabled")
        return

    updated = db.triggers.update(trigger.id, enabled=True)
    if updated:
        typer.echo(f"✓ Enabled trigger '{name}'")
    else:
        typer.echo(f"Error: Failed to enable trigger '{name}'", err=True)
        raise typer.Exit(1)


@app.command()
def disable(
    name: str = typer.Argument(..., help="Name of the trigger to disable"),
):
    """Disable a trigger"""
    db = get_db()
    trigger = db.triggers.get_by_name(name)

    if not trigger:
        typer.echo(f"Error: Trigger '{name}' not found", err=True)
        raise typer.Exit(1)

    if not trigger.enabled:
        typer.echo(f"Trigger '{name}' is already disabled")
        return

    updated = db.triggers.update(trigger.id, enabled=False)
    if updated:
        typer.echo(f"✓ Disabled trigger '{name}'")
    else:
        typer.echo(f"Error: Failed to disable trigger '{name}'", err=True)
        raise typer.Exit(1)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Name of the trigger to remove"),
):
    """Remove a trigger"""
    db = get_db()

    deleted = db.triggers.delete_by_name(name)
    if deleted:
        typer.echo(f"✓ Removed trigger '{name}'")
    else:
        typer.echo(f"Error: Trigger '{name}' not found", err=True)
        raise typer.Exit(1)


@app.command()
def reset():
    """Reset the trigger database"""
    db = get_db()
    db.triggers.delete_all()
    typer.echo("✓ Reset trigger database")
