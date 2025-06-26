import typer

from toolbox.db import conn
from toolbox.installer import (
    install_mcp,
    list_installed,
    list_apps_in_store,
    reset_mcp,
    show_mcp,
)
from toolbox.settings import settings

app = typer.Typer()


def install(
    name: str,
    use_local_deployments: bool = typer.Option(
        False, "--use-local-deployments", "-ld", help="Use local deployments"
    ),
    use_local_packages: bool = typer.Option(
        False, "--use-local-packages", "-lp", help="Use local packages"
    ),
    insert_syftbox_login: bool = typer.Option(
        False, "--insert-syftbox-login", "-il", help="Insert syftbox login"
    ),
    clients: list[str] = typer.Option(
        [], "--client", "-c", help="Client to install for"
    ),
):
    if use_local_deployments:
        settings.use_local_deployments = True
        print("USING LOCAL DEPLOYMENTS")
    if use_local_packages:
        settings.use_local_packages = True
        print("USING LOCAL PACKAGES")
    if insert_syftbox_login:
        settings.insert_syftbox_login = True
        print("INSERTING SYFTBOX LOGIN")
    install_mcp(conn, name, clients=clients)


def list():
    list_installed(conn)


def show(name: str):
    show_mcp(conn, name)


def list_store():
    list_apps_in_store()


def reset():
    reset_mcp(conn)


app.command()(install)
app.command()(list)
app.command()(show)
app.command()(reset)
app.command()(list_store)

if __name__ == "__main__":
    app()
