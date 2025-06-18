import json
import platform
import sqlite3

from pydantic import BaseModel
from tabulate import tabulate

from toolbox.db import db_get_mcps, db_upsert_mcp
from toolbox.installed_mcp import (
    HOME,
    INSTALLED_HEADERS,
    InstalledMCP,
    create_clickable_file_link,
)
from toolbox.store.installation_context import InstallationContext
from toolbox.store.store_code import STORE_ELEMENTS
from toolbox.store.store_json import check_name

CLAUDE_CONFIG_FILE = (
    f"{HOME}/Library/Application Support/Claude/claude_desktop_config.json"
)


class MCPConfigItem(BaseModel):
    name: str
    json_body: dict
    client: str


def current_claude_desktop_config():
    if platform.system() != "Darwin":
        raise RuntimeError("Currently only macOS is supported")
    with open(
        f"{HOME}/Library/Application Support/Claude/claude_desktop_config.json", "r"
    ) as f:
        return json.load(f)


def get_claude_config_items() -> list[MCPConfigItem]:
    full_json = current_claude_desktop_config()
    res = []
    for name, json_body in full_json["mcpServers"].items():
        res.append(
            MCPConfigItem(
                name=name,
                json_body=json_body,
                client="claude",
            )
        )
    return res


def install_mcp(
    conn: sqlite3.Connection,
    name: str,
    clients: list[str] | None = None,
    read_access: list[str] = None,
    write_access: list[str] = None,
    model: str | None = None,
    host: str | None = None,
    managed_by: str | None = None,
    proxy: str | None = None,
    verified: bool = False,
):
    if clients is None or isinstance(clients, list) and len(clients) == 0:
        print("no clients provided, installing to claude desktop by default\n")
        clients = ["claude"]

    for client in clients:
        check_name(name)

        store_element = STORE_ELEMENTS[name]
        callbacks = store_element.callbacks
        context = InstallationContext(callbacks=callbacks, values={})
        context.on_input()

        mcp = InstalledMCP.from_cli_args(
            name=name,
            client=client,
            read_access=read_access,
            write_access=write_access,
            model=model,
            host=host,
            managed_by=managed_by,
            proxy=proxy,
            context=context,
        )

        if client == "claude":
            add_mcp_to_claude_desktop_config(mcp)
            db_upsert_mcp(conn, mcp)
        else:
            print(f"skipping mcp for {client}, not supported yet")

    print(f"Successfully installed '{name}' for {', '.join(clients)}")
    print(f"Config files: {CLAUDE_CONFIG_FILE}")

    # launch mcp server. 3 options:
    # 1. local mcp server over stdio
    # 2. local mcp server over http (not for now?) -> requires daemon
    # 3. remote openmined mcp server over http


def list_installed(conn: sqlite3.Connection):
    mcps = db_get_mcps(conn)
    print(
        tabulate(
            [m.format_as_tabulate_row() for m in mcps],
            headers=INSTALLED_HEADERS,
            maxcolwidths=[8 for _ in INSTALLED_HEADERS] if len(mcps) > 0 else None,
            maxheadercolwidths=[6 for _ in INSTALLED_HEADERS]
            if len(mcps) > 0
            else None,
        )
    )
    if len(mcps) > 0:
        print(f"""
Clients:
[1]: {create_clickable_file_link(CLAUDE_CONFIG_FILE)}
""")


def add_mcp_to_claude_desktop_config(mcp: InstalledMCP):
    claude_desktop_config = current_claude_desktop_config()
    if mcp.json_body is not None:
        claude_desktop_config["mcpServers"][mcp.name] = mcp.json_body
        with open(CLAUDE_CONFIG_FILE, "w") as f:
            json.dump(claude_desktop_config, f, indent=4)


# def handle_secret_request(secret_request: dict):
#     if secret_request["request_type"] == "text_input" and secret_request["result_type"] == "env":
#         secret = TextInputEnvRequestedSecret(
#             result_name=secret_request["result_name"],
#             request_text=secret_request["request_text"]
#         )
#         secret.run_input_flow()
#         return secret
#     else:
#         raise ValueError(f"Unsupported secret request type: {secret_request['result_type']}")
