from pathlib import Path

import typer
from rich.console import Console
from sqlalchemy.exc import IntegrityError

from toolbox.triggers.trigger_store import get_db

console = Console()

app = typer.Typer(no_args_is_help=True)


def print_execution(execution):
    """Print a single execution with simple formatting"""
    if execution.completed_at:
        status_icon = "✓" if execution.exit_code == 0 else "✗"
        status_color = "green" if execution.exit_code == 0 else "red"

        console.print(
            f"[{status_color}]{status_icon}[/{status_color}] {execution.completed_at} (exit code: {execution.exit_code})"
        )

        if execution.logs.strip():
            console.print(execution.logs.strip())
        else:
            console.print("[dim]No logs[/dim]")
    else:
        console.print(f"⏳ {execution.created_at} [yellow](running)[/yellow]")


@app.command()
def add(
    name: str | None = typer.Option(None, "--name", "-n", help="Name of the trigger"),
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
    path = Path(script_path).expanduser().resolve().absolute()
    if not path.exists():
        typer.echo(f"Error: Script path '{script_path}' does not exist", err=True)
        raise typer.Exit(1)

    if not path.is_file():
        typer.echo(f"Error: '{script_path}' is not a file", err=True)
        raise typer.Exit(1)

    try:
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
    num_executions: int = typer.Option(
        1, "--num-executions", "-n", help="Number of recent executions to show"
    ),
):
    """Show a trigger with recent executions"""
    db = get_db()
    trigger = db.triggers.get_by_name(name)

    if not trigger:
        typer.echo(f"Error: Trigger '{name}' not found", err=True)
        raise typer.Exit(1)

    # Show trigger info
    status_color = "green" if trigger.enabled else "red"
    status_text = "enabled" if trigger.enabled else "disabled"

    console.print(f"[bold blue]Trigger: {trigger.name}[/bold blue]")
    console.print(f"  [bold]ID:[/bold] {trigger.id}")
    console.print(
        f"  [bold]Status:[/bold] [{status_color}]{status_text}[/{status_color}]"
    )
    console.print(f"  [bold]Schedule:[/bold] {trigger.cron_schedule}")
    console.print(f"  [bold]Script:[/bold] {trigger.script_path}")
    console.print(f"  [bold]Created:[/bold] {trigger.created_at}")

    # Show recent executions
    executions = db.executions.get_all(trigger_id=trigger.id, limit=num_executions)
    if executions:
        console.print(f"\n[bold]Recent executions (showing {len(executions)}):[/bold]")

        for i, ex in enumerate(executions):
            print_execution(ex)

            # Add spacing between executions if showing multiple
            if i < len(executions) - 1:
                console.print()
    else:
        console.print("\n[dim]No executions found[/dim]")


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
