import typer
from toolbox.db import conn
from toolbox.installer import install_mcp, list_installed, show_mcp

app = typer.Typer()


def install(
    name: str,
    clients: list[str] = typer.Option(
        [], "--client", "-c", help="Client to install for"
    ),
):
    install_mcp(conn, name, clients=clients)


def list():
    list_installed(conn)


def show(name: str):
    show_mcp(conn, name)


app.command()(install)
app.command()(list)
app.command()(show)


if __name__ == "__main__":
    app()
