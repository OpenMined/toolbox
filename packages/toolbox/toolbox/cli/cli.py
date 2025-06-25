import typer
from toolbox.db import conn
from toolbox.installer import install_mcp, list_installed, show_mcp, reset_mcp
from toolbox.settings import settings

app = typer.Typer()


def install(
    name: str,
    use_local_deployments: bool = typer.Option(
        False, "--use-local-deployments", "-l", help="Use local deployments"
    ),
    clients: list[str] = typer.Option(
        [], "--client", "-c", help="Client to install for"
    ),
):
    
    if use_local_deployments:
        settings.use_local_deployments = True
        print("USING LOCAL DEPLOYMENTS")
    install_mcp(conn, name, clients=clients)


def list():
    list_installed(conn)


def show(name: str):
    show_mcp(conn, name)
    
def reset():
    reset_mcp()


app.command()(install)
app.command()(list)
app.command()(show)
app.command()(reset)

if __name__ == "__main__":
    app()
