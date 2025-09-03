import subprocess
from pathlib import Path

import typer
from rich.console import Console

from toolbox.analytics import track_cli_command
from toolbox.daemon.daemon import (
    is_daemon_running,
    run_daemon,
    stop_daemon,
)
from toolbox.launchd import add_to_launchd, is_daemon_installed, remove_from_launchd
from toolbox.settings import settings

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def run_foreground(
    log_file: Path | None = typer.Option(
        None, "--log-file", help="Override log file path"
    ),
    host: str | None = typer.Option(None, "--host", help="Host to bind to"),
    port: int | None = typer.Option(None, "--port", help="Port to bind to"),
    log_to_file: bool = typer.Option(
        True,
        "--log-to-file/--no-log-to-file",
        "-l/-nl",
        help="Enable logging to file. If False, logs will be printed to stdout.",
    ),
):
    """Run the toolbox daemon in foreground"""

    run_daemon(
        host=host,
        port=port,
        log_file=log_file,
        log_to_file=log_to_file,
    )


@app.command()
@track_cli_command("daemon start")
def start(
    host: str | None = typer.Option(None, "--host", help="Host to bind to"),
    port: int | None = typer.Option(None, "--port", help="Port to bind to"),
):
    """Start the toolbox daemon in background. Should only be used if daemon is not managed by launchd."""

    if is_daemon_running():
        console.print("[yellow]Daemon is already running[/yellow]")
        return

    # Build command with only provided options
    cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "toolbox.cli.daemon_cli",
        "run-foreground",
    ]

    if host is not None:
        cmd.extend(["--host", host])
    if port is not None:
        cmd.extend(["--port", str(port)])

    console.print("[cyan]Starting toolbox daemon in background...[/cyan]")
    subprocess.Popen(cmd, start_new_session=True)


@app.command()
@track_cli_command("daemon stop")
def stop():
    """Stop the toolbox daemon"""
    if not is_daemon_running():
        console.print("[yellow]Daemon is not running[/yellow]")
        return

    console.print("[cyan]Stopping toolbox daemon...[/cyan]")
    if stop_daemon():
        console.print("[green]✅ Daemon stopped successfully[/green]")
    else:
        console.print("[red]❌ Failed to stop daemon[/red]")


@app.command()
@track_cli_command("daemon status")
def status():
    """Check daemon status"""
    if is_daemon_running():
        with open(settings.daemon.pid_file, "r") as f:
            pid = f.read().strip()
        console.print(f"[green]✅ Daemon is running[/green] (PID: [cyan]{pid}[/cyan])")
    else:
        console.print("[yellow]⚠️  Daemon is not running[/yellow]")


@app.command()
@track_cli_command("daemon install")
def install():
    """Install toolbox daemon to launchd for automatic startup"""

    if is_daemon_installed():
        console.print("[yellow]Daemon is already installed[/yellow]")
        return

    try:
        add_to_launchd()
        console.print(
            "[green]✅ Daemon installed to launchd and will run automatically[/green]"
        )
        console.print("   To uninstall: [cyan]tb daemon uninstall[/cyan]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
@track_cli_command("daemon uninstall")
def uninstall():
    """Remove toolbox daemon from launchd"""
    if not is_daemon_installed():
        console.print("[yellow]Daemon is not installed[/yellow]")
        return

    try:
        plist_path = remove_from_launchd()
        console.print(f"[green]✅ Daemon removed from launchd at {plist_path}[/green]")
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
