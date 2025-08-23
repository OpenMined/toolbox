from pathlib import Path

import typer
from rich.console import Console

from toolbox.analytics import track_cli_command
from toolbox.daemon.daemon import (
    get_daemon_pid_file,
    is_daemon_running,
    run_daemon,
    stop_daemon,
)
from toolbox.launchd import add_to_launchd, is_daemon_installed, remove_from_launchd

app = typer.Typer(no_args_is_help=True)


@app.command()
def run_foreground(
    log_file: Path | None = typer.Option(None, "--log-file"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
):
    """Run the toolbox daemon in foreground"""

    pid_file = get_daemon_pid_file()
    run_daemon(
        host=host,
        port=port,
        log_file=log_file,
        pid_file=pid_file,
    )


@app.command()
@track_cli_command("daemon start")
def start(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
):
    """Start the toolbox daemon in background"""
    import subprocess

    pid_file = get_daemon_pid_file()
    if is_daemon_running(pid_file=pid_file):
        print("Daemon is already running")
        return

    logfile = Path.home() / ".toolbox" / "daemon.log"

    print("Starting toolbox daemon in background...")
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
            "--host",
            host,
            "--port",
            str(port),
        ],
        start_new_session=True,
    )
    print(f"Daemon started in background (logs: {logfile})")


@app.command()
@track_cli_command("daemon stop")
def stop():
    """Stop the toolbox daemon"""
    pid_file = get_daemon_pid_file()

    if not is_daemon_running(pid_file=pid_file):
        print("Daemon is not running")
        return

    print("Stopping toolbox daemon...")
    if stop_daemon(pid_file=pid_file):
        print("Daemon stopped successfully")
    else:
        print("Failed to stop daemon")


@app.command()
@track_cli_command("daemon status")
def status():
    """Check daemon status"""

    pid_file = get_daemon_pid_file()
    if is_daemon_running(pid_file=pid_file):
        with open(pid_file, "r") as f:
            pid = f.read().strip()
        print(f"Daemon is running (PID: {pid})")
    else:
        print("Daemon is not running")


@app.command()
@track_cli_command("daemon install")
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
@track_cli_command("daemon uninstall")
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
