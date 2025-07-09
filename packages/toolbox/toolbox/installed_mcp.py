from __future__ import annotations

import json
import shutil
import sqlite3
import time
import urllib
from pathlib import Path
from typing import TYPE_CHECKING

from toolbox import db
from pydantic import BaseModel

from toolbox.mcp_clients.mcp_clients import (
    current_claude_desktop_config,
    write_claude_desktop_config,
)
from toolbox.mcp_installer.mcp_installer import pkill_f, process_exists
from toolbox.store.store_code import STORE_ELEMENTS
from toolbox.store.store_json import STORE, get_default_setting
from toolbox.utils.healthcheck import HealthStatus, healthcheck
from toolbox.utils.utils import DEFAULT_LOG_FILE, installation_dir_from_name

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext

HOME = Path.home()
INSTALLED_HEADERS = [
    "TYPE",
    "NAME",
    "MANAGED BY",
    "CLIENT",
    "ACCESS",
    "READ ACCESS",
    "WRITE ACCESS",
    "CLIENT CONFIG",
]

HEALTH_STATUS_ICON = {
    HealthStatus.HEALTHY: "🟢",
    HealthStatus.UNHEALTHY: "🔴",
    HealthStatus.UNKNOWN: "🟠",
}

ANSI_BOLD = "\x1b[1m"
ANSI_GREEN = "\x1b[32m"
ANSI_RED = "\x1b[31m"
ANSI_YELLOW = "\x1b[33m"
ANSI_RESET = "\x1b[0m"


class InstalledMCP(BaseModel):
    name: str
    client: str
    read_access: list[str]
    write_access: list[str]
    model: str | None = None
    host: str
    managed_by: str
    proxy: str | None = None
    verified: bool
    json_body: dict | None = None
    deployment_method: str
    has_client_json: bool = True
    deployment: dict
    settings: dict
    app_type: str

    @property
    def client_config_file(self) -> str:
        if self.client == "claude":
            return "[1]"
        else:
            raise ValueError(f"Client {self.client} not supported")

    @property
    def is_running(self) -> bool:
        module = self.deployment.get("module", None)
        if module is None:
            return False
        return process_exists(module)

    @property
    def status_icon(self) -> str:
        if self.managed_by.lower() == "claude":
            return "🟢"

        healthy = healthcheck(self)
        return HEALTH_STATUS_ICON[healthy]

    @property
    def status_str(self) -> str:
        icon = self.status_icon
        if icon == "🟢":
            return icon
        else:
            return f"{icon} (unreachable)"

    @property
    def installation_dir(self) -> Path:
        return installation_dir_from_name(self.name)

    @property
    def log_file(self) -> Path:
        return self.installation_dir / DEFAULT_LOG_FILE

    def format_as_tabulate_row(self) -> list[str]:
        return [
            self.app_type,
            f"{self.name}",
            f"{self.managed_by} {self.status_icon}",
            self.client,
            self.deployment_method,
            ",\n".join(self.read_access),
            ",\n".join(self.write_access),
            self.client_config_file,
        ]

    @classmethod
    def from_cli_args(
        cls,
        name: str,
        client: str,
        read_access: list[str] | None = None,
        write_access: list[str] | None = None,
        model: str | None = None,
        host: str | None = None,
        managed_by: str | None = None,
        proxy: str | None = None,
        deployment_method: str | None = None,
        context: InstallationContext = None,
    ):
        if name not in STORE:
            raise ValueError(
                f"{name} not found in store, store has entries: {list(STORE.keys())}"
            )

        if read_access is None:
            read_access = get_default_setting(name, client, "read_access")
        if write_access is None:
            write_access = get_default_setting(name, client, "write_access")
        if model is None:
            model = get_default_setting(name, client, "model")
        if host is None:
            host = get_default_setting(name, client, "host")
        if managed_by is None:
            managed_by = get_default_setting(name, client, "managed_by")
        if proxy is None:
            proxy = get_default_setting(name, client, "proxy")

        verified = get_default_setting(name, client, "verified")
        app_type = get_default_setting(name, client, "app_type")

        if deployment_method is None:
            deployment_method = get_default_setting(name, client, "deployment_method")

        deployment = STORE[name].get("deployment", {})

        has_mcp = STORE[name].get("has_client_json", True)
        if not has_mcp:
            json_body = {}
        else:
            json_bodies_for_client_for_deployment_method = STORE[name][
                "json_bodies_for_client_for_deployment_method"
            ]
            if "all" in json_bodies_for_client_for_deployment_method:
                jsons_bodies_for_deployment_methods = (
                    json_bodies_for_client_for_deployment_method["all"]
                )
            elif client in json_bodies_for_client_for_deployment_method:
                jsons_bodies_for_deployment_methods = (
                    json_bodies_for_client_for_deployment_method[client]
                )
            else:
                raise ValueError(
                    f"{client} is not a valid client, valid clients are: {list(json_bodies_for_client_for_deployment_method.keys())}"
                )

            if deployment_method not in jsons_bodies_for_deployment_methods:
                raise ValueError(
                    f"The chosen deployment method is not available for {client}"
                )

            json_body = jsons_bodies_for_deployment_methods[deployment_method]

        context.on_install_init(json_body)

        return cls(
            name=name,
            client=client,
            read_access=read_access,
            write_access=write_access,
            model=model,
            host=host,
            managed_by=managed_by,
            proxy=proxy,
            verified=verified,
            json_body=json_body,
            deployment_method=deployment_method,
            deployment=deployment,
            settings=context.context_settings,
            has_client_json=has_mcp,
            app_type=app_type,
        )

    def delete(self, conn: sqlite3.Connection):
        store_object = STORE_ELEMENTS[self.name]
        callbacks = store_object.callbacks
        for callback in callbacks:
            callback.on_delete(self)

        if self.installation_dir.exists():
            shutil.rmtree(self.installation_dir, ignore_errors=True)
        db.db_delete_mcp(conn, self.name)
        if self.is_running:
            module_name = self.deployment.get("module", None)
            if module_name is not None:
                pkill_f(module_name)
            else:
                print(f"No module name found for {self.name}")
        self.remove_from_client_config()

    def remove_from_client_config(self) -> str:
        if self.client == "claude":
            client_config = current_claude_desktop_config()
            if self.name in client_config["mcpServers"]:
                del client_config["mcpServers"][self.name]
                write_claude_desktop_config(client_config)
        else:
            raise ValueError(f"Client {self.client} not supported")

    @classmethod
    def from_db_row(cls, row: sqlite3.Row):
        row = dict(row)
        row["client"] = json.loads(row["client"])
        row["read_access"] = json.loads(row["read_access"])
        row["write_access"] = json.loads(row["write_access"])
        row["json_body"] = json.loads(row["json_body"])
        row["deployment_method"] = row["deployment_method"]
        row["deployment"] = json.loads(row["deployment"])
        row["settings"] = json.loads(row["settings"])
        row["app_type"] = row["app_type"]
        return cls(**row)

    def external_dependency_status_checks(self) -> dict:
        status_dict = {}
        for callback in STORE_ELEMENTS[self.name].callbacks:
            res = callback.on_external_dependency_status_check(self)
            if res is not None:
                status_dict.update(res)
        return status_dict

    def external_dependency_check_str(self) -> str:
        status_dict = self.external_dependency_status_checks()
        status_str = "\n".join(
            [f"{key}: {value}" for key, value in status_dict.items()]
        )
        if status_str == "":
            return ""
        else:
            return f"""
{ANSI_BOLD}external dependency status:{ANSI_RESET}
{status_str}
"""

    def log(self, follow: bool = False):
        if self.log_file.exists():
            if follow:
                with open(self.log_file, "r") as f:
                    while True:
                        line = f.readline()
                        if line == "":
                            time.sleep(0.1)
                        else:
                            print(line, end="")
            else:
                with open(self.log_file, "r") as f:
                    print(f.read())
        else:
            print(f"No log file found for {self.name}")

    def logs_str(self) -> str:
        MAX_LOG_LINES = 5
        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                logs = f.read()
            if logs.count("\n") > MAX_LOG_LINES:
                last_lines = logs.split("\n")[-MAX_LOG_LINES:]
                last_lines_str = "\n".join(last_lines)
                logs = f"...(cut off)\n{last_lines_str}"
        else:
            logs = "No logs available"
        return f"""        
{ANSI_BOLD}Logs:{ANSI_RESET} ({self.log_file})

{logs}
"""

    def data_stats_str(self) -> str:
        callbacks = STORE_ELEMENTS[self.name].callbacks
        res = {}
        for callback in callbacks:
            callback_res = callback.on_data_stats(self)
            if callback_res is not None:
                res.update(callback_res)
        return "\n".join([f"{key}: {value}" for key, value in res.items()])

    def settings_str(self) -> str:
        setting_values_str = "\n".join(
            [f"{key}: {value}" for key, value in self.settings.items()]
        )
        return f"""
{ANSI_BOLD}Settings:{ANSI_RESET}
{setting_values_str}
"""

    def show(self, settings: bool = False):
        settings_str = ""
        if settings:
            settings_str = self.settings_str()
        print(f"""
{ANSI_GREEN}{self.name}{ANSI_RESET} {self.status_str}
{self.external_dependency_check_str()}
{self.data_stats_str()}
{settings_str}
{self.logs_str()}
""")


def create_clickable_file_link(file_path, link_text="LINK"):
    abs_path = urllib.parse.quote(file_path)
    file_url = f"file://{abs_path}"
    return file_url
