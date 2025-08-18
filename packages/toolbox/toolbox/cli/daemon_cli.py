import subprocess
from pathlib import Path

import typer
from rich.console import Console

from toolbox.launchd import add_to_launchd, is_daemon_installed, remove_from_launchd
from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import get_db

app = typer.Typer(no_args_is_help=True)


@app.command()
def run_foreground(log_file: Path = typer.Option(None, "--log-file")):
    """Run the toolbox daemon in foreground"""
    trigger_db = get_db()
    scheduler = Scheduler(trigger_db)
    if log_file is None:
        log_file = scheduler.pid_file.parent / "scheduler.log"
    scheduler.run(log_file=log_file)


@app.command()
def start():
    """Start the toolbox daemon in background"""
    trigger_db = get_db()
    scheduler = Scheduler(trigger_db)

    if scheduler.is_running():
        print("Scheduler is already running")
        return

    logfile = scheduler.pid_file.parent / "scheduler.log"

    print("Starting trigger daemon in background...")
    subprocess.Popen(
        [
            "uv",
            "run",
            "python",
            "-m",
            "toolbox.cli.daemon_cli",
            "run-foreground",
            "--log-file",
            str(logfile),
        ],
        start_new_session=True,
    )
    print(f"Scheduler started in background (logs: {logfile})")


@app.command()
def stop():
    """Stop the toolbox daemon"""
    trigger_db = get_db()
    scheduler = Scheduler(trigger_db)

    if not scheduler.is_running():
        print("Scheduler is not running")
        return

    print("Stopping trigger daemon...")
    if scheduler.stop():
        print("Scheduler stopped successfully")
    else:
        print("Failed to stop scheduler")


@app.command()
def status():
    """Check daemon status"""
    trigger_db = get_db()
    scheduler = Scheduler(trigger_db)

    if scheduler.is_running():
        with open(scheduler.pid_file, "r") as f:
            pid = f.read().strip()
        print(f"Scheduler is running (PID: {pid})")
    else:
        print("Scheduler is not running")


@app.command()
def install():
    """Install toolbox daemon to launchd for automatic startup"""
    console = Console()

    if is_daemon_installed():
        console.print("[yellow]Daemon is already installed[/yellow]")
        return

    try:
        add_to_launchd()
        console.print(
            "[green]✅ Daemon installed to launchd and will run automatically[/green]"
        )
        console.print("   To uninstall: [yellow]tb daemon uninstall[/yellow]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def uninstall():
    """Remove toolbox daemon from launchd"""
    console = Console()
    if not is_daemon_installed():
        console.print("[yellow]Daemon is not installed[/yellow]")
        return

    try:
        plist_path = remove_from_launchd()
        console.print(f"[green]Daemon removed from launchd at {plist_path}[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
