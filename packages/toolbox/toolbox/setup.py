from functools import wraps

import typer
from rich.console import Console
from rich.panel import Panel

from toolbox.settings import settings


def setup_required(func):
    """Decorator that runs setup if this is the first time using toolbox"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if settings.first_time_setup:
            run_setup()
        return func(*args, **kwargs)

    return wrapper


WELCOME_MESSAGE = """🧰 Welcome to Toolbox!

A privacy-first tool to install MCP servers and background agents for your personal data.

• Install MCP servers with [cyan]tb install <app_name>[/cyan]
• List available apps with [cyan]tb list-store[/cyan]  
• View installed apps with [cyan]tb list[/cyan]"""


ANALYTICS_MESSAGE = """[yellow]📊 Help us improve Toolbox[/yellow]

We collect anonymous analytics to understand:
[dim]• Which MCP servers are most popular
• How the CLI is used
• No personal data is collected[/dim]"""


def run_setup():
    console = Console()

    # Show welcome message
    console.print(
        Panel(WELCOME_MESSAGE, title="Toolbox", border_style="blue", padding=(1, 2))
    )

    # Install daemon
    from toolbox.cli.daemon_cli import install as daemon_install

    daemon_install()

    console.print()
    console.print(ANALYTICS_MESSAGE)

    if typer.confirm("Disable analytics?", default=False):
        settings.analytics_enabled = False
    else:
        settings.analytics_enabled = True

    settings.save()
    console.print(
        "Setup complete, your config is saved to [yellow]~/.toolbox/config.json[/yellow]"
    )
