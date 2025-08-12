import typer

from toolbox.cli import daemon_cli, trigger_cli
from toolbox.db import conn
from toolbox.installer import (
    call_mcp,
    install_mcp,
    list_apps_in_store,
    list_installed,
    log_mcp,
    reset_mcp,
    show_mcp,
    start_mcp_and_requirements,
    stop_mcp,
)
from toolbox.settings import settings
from toolbox.store.store_json import STORE

app = typer.Typer(no_args_is_help=True)


def install(
    name: str,
    use_local_deployments: bool = typer.Option(
        False, "--use-local-deployments", "-ld", help="Use local deployments"
    ),
    use_local_packages: bool = typer.Option(
        False, "--use-local-packages", "-lp", help="Use local packages"
    ),
    request_syftbox_login: bool = typer.Option(
        False, "--request-syftbox-login", "-rl", help="Request syftbox login"
    ),
    clients: list[str] = typer.Option(
        [], "--client", "-c", help="Client to install for"
    ),
):
    if use_local_deployments:
        # TOOD: FIX
        settings.use_local_deployments = True
        STORE["meeting-notes-mcp"]["context_settings"]["notes_webserver_url"] = (
            "http://localhost:8000/"
        )
        # print("USING LOCAL DEPLOYMENTS")
    if use_local_packages:
        settings.use_local_packages = True
        # print("USING LOCAL PACKAGES")
    if request_syftbox_login:
        settings.request_syftbox_login = True
        print("REQUESTING SYFTBOX LOGIN")
    install_mcp(conn, name, clients=clients)


def list():
    list_installed(conn)


def show(name: str, settings: bool = typer.Option(False, "--settings", "-s")):
    show_mcp(conn, name, settings=settings)


def start(name: str):
    start_mcp_and_requirements(name, conn)


def stop(name: str):
    stop_mcp(name, conn)


def list_store():
    list_apps_in_store()


def reset():
    reset_mcp(conn)

    from toolbox.cli.daemon_cli import uninstall

    uninstall(confirm=True)


def log(name: str, follow: bool = typer.Option(False, "--follow", "-f")):
    log_mcp(conn, name, follow=follow)


def call(app_name: str, endpoint: str):
    call_mcp(conn, app_name, endpoint)


app.command()(list_store)
app.command()(install)
app.command()(list)
app.command()(show)
app.command()(log)
app.command()(reset)
app.command()(call)
app.command()(start)
app.command()(stop)

# Add subgroups
app.add_typer(daemon_cli.app, name="daemon", help="Daemon management commands")
app.add_typer(trigger_cli.app, name="trigger", help="Trigger management commands")


if __name__ == "__main__":
    app()
