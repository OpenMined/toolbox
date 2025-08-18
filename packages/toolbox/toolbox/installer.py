import json
import platform
import secrets
import shutil
import sqlite3
import textwrap
from pathlib import Path

import requests
from pydantic import BaseModel
from tabulate import tabulate

from toolbox.db import db_get_mcps, db_get_mcps_by_name, db_upsert_mcp
from toolbox.external_dependencies.external_depenencies import (
    get_existing_syftbox_email_from_config,
)
from toolbox.installed_mcp import (
    HOME,
    INSTALLED_HEADERS,
    InstalledMCP,
    create_clickable_file_link,
)
from toolbox.mcp_clients.mcp_clients import (
    CLAUDE_CONFIG_FILE,
    check_mcp_client_installation,
    current_claude_desktop_config,
)
from toolbox.settings import settings
from toolbox.store.installation_context import InstallationContext
from toolbox.store.store_code import STORE_ELEMENTS
from toolbox.store.store_json import STORE, check_name
from toolbox.toolbox_requirements import has_npx, has_uv


def get_requirements(name: str):
    store_json = STORE[name]
    if "requirements" in store_json:
        return store_json["requirements"]
    else:
        return []


def install_requirements(
    conn: sqlite3.Connection,
    name: str,
    context: InstallationContext,
    clients: list[str],
):
    store_json = STORE[name]
    for requirement in get_requirements(name):
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
        context.context_settings.update(requirement_context.context_settings)
        context.context_apps.append(requirement)


def check_external_dependencies(
    name: str,
    context: InstallationContext,
):
    store_element = STORE_ELEMENTS[name]
    for callback in store_element.callbacks:
        callback.on_external_dependency_check(context)


def check_toolbox_requirements():
    if not has_uv():
        res = input("uv is not installed. Please install uv first. Continue? (y/n)")
        if res != "y":
            exit(1)
    if not has_npx():
        res = input("npx is not installed. Please install npx first. Continue? (y/n)")
        if res != "y":
            exit(1)


def add_syftbox_config_to_context(context: InstallationContext):
    email = get_existing_syftbox_email_from_config()
    if email is not None:
        # use a random secret here

        context.context_dict["syftbox_email"] = email
        context.context_settings["SYFTBOX_EMAIL"] = email
        syftbox_access_token = secrets.token_hex(8)
        context.context_dict["syftbox_access_token"] = syftbox_access_token
        context.context_settings["SYFTBOX_ACCESS_TOKEN"] = syftbox_access_token


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
    for client in clients:
        check_mcp_client_installation(client)

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

    context.on_install_start()

    if not settings.request_syftbox_login:
        add_syftbox_config_to_context(context)

    install_requirements(conn, name, context, clients)
    check_external_dependencies(name, context)
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

            context.on_run_mcp()
            db_upsert_mcp(conn, mcp)
        else:
            print(f"skipping mcp for {client}, not supported yet")

    print(f"Successfully installed '{name}' for {', '.join(clients)}")
    print(f"Config files: {CLAUDE_CONFIG_FILE}\n")

    # launch mcp server. 3 options:
    # 1. local mcp server over stdio
    # 2. local mcp server over http (not for now?) -> requires daemon
    # 3. remote openmined mcp server over http


def stop_mcp(name: str, conn: sqlite3.Connection):
    mcp = get_mcp_by_fuzzy_name(conn, name)
    mcp.stop()
    print(f"Stopped MCP: {mcp.name}")


def start_mcp(name: str, conn: sqlite3.Connection):
    mcp = get_mcp_by_fuzzy_name(conn, name)
    store_element = STORE_ELEMENTS[mcp.name]
    callbacks = store_element.callbacks
    context = InstallationContext(
        callbacks=callbacks,
        context_dict={},
        current_app=mcp.name,
        context_apps=[mcp.name],
        context_settings=mcp.settings,
    )

    context.on_run_mcp()


def start_mcp_and_requirements(name: str, conn: sqlite3.Connection):
    mcp = get_mcp_by_fuzzy_name(conn, name)

    for requirement in get_requirements(mcp.name):
        req_mcp = get_mcp_by_fuzzy_name(conn, requirement)
        if not req_mcp.is_running:
            print(f"Starting requirement: {req_mcp.name}")
            start_mcp(requirement, conn)

    if not mcp.is_running:
        print(f"Starting MCP: {mcp.name}")
        start_mcp(mcp.name, conn)
    else:
        print(f"MCP {mcp.name} is already running")


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


def list_apps_in_store():
    store_data = []
    for name, store_json in STORE.items():
        requirements_str = ", ".join(store_json.get("requirements", []))
        external_dependencies_str = ", ".join(
            store_json.get("external_dependencies", [])
        )
        url = store_json.get("url", "")
        store_data.append(
            [
                name,
                store_json["default_settings"]["default_deployment_method"],
                external_dependencies_str,
                requirements_str,
                url,
            ]
        )

    print(
        tabulate(
            store_data,
            headers=[
                "Name",
                "Deployment",
                "External Dependencies",
                "Requirements",
                "URL",
            ],
            maxcolwidths=[20, 15, 15, 15, 100],
            maxheadercolwidths=[20, 15, 15, 15, 100],
            tablefmt="grid",
        )
    )


def get_mcp_by_fuzzy_name(conn: sqlite3.Connection, name: str):
    mcps = db_get_mcps_by_name(conn, name)
    if len(mcps) == 0:
        mcps = db_get_mcps(conn)
        matches = []
        for mcp in mcps:
            if name in mcp.name:
                matches.append(mcp)
        if len(matches) == 0:
            raise ValueError(f"No MCPs found for {name}")
        elif len(matches) == 1:
            mcp = matches[0]
        else:
            print(f"Multiple MCPs found for {name}:")
            raise ValueError(f"Multiple MCPs found for {name}")

    elif len(mcps) == 1:
        mcp = mcps[0]
    else:
        raise ValueError(f"Multiple MCPs found for {name}")
    return mcp


def show_mcp(conn: sqlite3.Connection, name: str, settings: bool = False):
    mcp = get_mcp_by_fuzzy_name(conn, name)
    mcp.show(settings=settings)


def reset_mcp(conn: sqlite3.Connection):
    """Reset MCP installation by removing the toolbox directory and clearing database."""
    # Remove the toolbox directory

    for mcp in db_get_mcps(conn):
        mcp.delete(conn)
    toolbox_dir = Path.home() / ".toolbox"
    if toolbox_dir.exists():
        shutil.rmtree(toolbox_dir, ignore_errors=True)
        print(f"Reset toolbox directory: {toolbox_dir}")


def log_mcp(conn: sqlite3.Connection, name: str, follow: bool = False):
    mcp = get_mcp_by_fuzzy_name(conn, name)
    mcp.log(follow=follow)


def call_mcp(conn: sqlite3.Connection, name: str, endpoint: str):
    res = requests.post(f"http://localhost:8002/{endpoint}")
    print(res.json())


def add_mcp_to_claude_desktop_config(mcp: InstalledMCP):
    claude_desktop_config = current_claude_desktop_config()
    if mcp.json_body is not None:
        if "mcpServers" not in claude_desktop_config:
            claude_desktop_config["mcpServers"] = {}
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
