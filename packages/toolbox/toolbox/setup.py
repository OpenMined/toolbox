import typer
from rich.console import Console
from rich.panel import Panel

from toolbox.settings import settings

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

NOTIFICATION_MESSAGE = f"""[yellow]📱 Notifications[/yellow]
Toolbox triggers can send you notifications with ntfy.sh

Your default notification topic is [yellow]{settings.default_notification_topic}[/yellow]
To change this, run [cyan]tb set-notification-topic <topic>[/cyan].

To receive notifications on your phone, install [link=https://ntfy.sh]ntfy.sh[/link] and subscribe to your topic.
"""


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
    if settings.dev_mode:
        settings.analytics_enabled = False
    elif typer.confirm("Disable analytics?", default=False):
        settings.analytics_enabled = False
    else:
        settings.analytics_enabled = True

    console.print()
    console.print(NOTIFICATION_MESSAGE)
    console.print()

    settings.save()
    console.print(
        "Setup complete, your config is saved to [yellow]~/.toolbox/config.json[/yellow]"
    )
