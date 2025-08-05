import subprocess
from pathlib import Path

import typer

from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import get_db

app = typer.Typer(no_args_is_help=True)


@app.command()
def run_foreground(log_file: Path = typer.Option(None, "--log-file")):
    """Run the trigger daemon in foreground"""
    trigger_db = get_db()
    scheduler = Scheduler(trigger_db)
    scheduler.run(log_file=log_file)


@app.command()
def start():
    """Start the trigger daemon in background"""
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
    """Stop the trigger daemon"""
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


if __name__ == "__main__":
    app()
