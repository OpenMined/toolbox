import json
import platform
import sqlite3

from pydantic import BaseModel
from tabulate import tabulate

from toolbox.db import db_get_mcps, db_get_mcps_by_name, db_upsert_mcp
from toolbox.installed_mcp import (
    HOME,
    INSTALLED_HEADERS,
    InstalledMCP,
    create_clickable_file_link,
)
from toolbox.store.installation_context import InstallationContext
from toolbox.store.store_code import STORE_ELEMENTS
from toolbox.store.store_json import STORE, check_name

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


def install_requirements(
    conn: sqlite3.Connection,
    name: str,
    context: InstallationContext,
    clients: list[str],
):
    store_json = STORE[name]
    if "requirements" in store_json:
        for requirement in store_json["requirements"]:
            print(f"{name} requires {requirement}, installing...")

            store_element = STORE_ELEMENTS[requirement]

            callbacks = store_element.callbacks
            requirement_context = InstallationContext(
                callbacks=callbacks,
                context_dict=context.context_dict,
                current_app=requirement,
                context_apps=context.context_apps + [requirement],
                context_settings=store_json.get("context_settings", {}),
            )
            install_mcp(conn, requirement, clients=clients, context=requirement_context)
            context.context_dict.update(requirement_context.context_dict)
            context.context_apps.append(requirement)


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
    context: InstallationContext | None = None,
):
    if clients is None or isinstance(clients, list) and len(clients) == 0:
        print("no clients provided, installing to claude desktop by default\n")
        clients = ["claude"]

    check_name(name)
    store_element = STORE_ELEMENTS[name]
    store_json = STORE[name]

    callbacks = store_element.callbacks

    if context is None:
        context = InstallationContext(
            callbacks=callbacks,
            context_dict={},
            current_app=name,
            context_apps=[name],
            context_settings=store_json.get("context_settings", {}),
        )

    install_requirements(conn, name, context, clients)
    context.on_input()

    for client in clients:
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
        context.mcp = mcp

        if client == "claude":
            if mcp.has_client_json:
                add_mcp_to_claude_desktop_config(mcp)
            context.on_install_init_finished()
            db_upsert_mcp(conn, mcp)
        else:
            print(f"skipping mcp for {client}, not supported yet")

    print(f"Successfully installed '{name}' for {', '.join(clients)}")
    print(f"Config files: {CLAUDE_CONFIG_FILE}\n")

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


def show_mcp(conn: sqlite3.Connection, name: str):
    mcps = db_get_mcps_by_name(conn, name)
    if len(mcps) == 0:
        print("No MCPs found for", name)
    elif len(mcps) == 1:
        mcp = mcps[0]
        mcp.show()
    else:
        raise ValueError(f"Multiple MCPs found for {name}")


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
