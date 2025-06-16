import typer
from toolbox.db import conn
from toolbox.installer import install_mcp, list_installed

app = typer.Typer()



def install(
    name: str,
    clients: list[str] = typer.Option([], "--client", "-c", help="Client to install for")
    ):
    install_mcp(conn, name, clients=clients)
    
    

def list():
    list_installed(conn)


app.command()(install)
app.command()(list)


if __name__ == "__main__":
    app()
