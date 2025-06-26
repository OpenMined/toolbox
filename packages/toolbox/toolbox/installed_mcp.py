from __future__ import annotations

import json
import shutil
import sqlite3
import urllib
from pathlib import Path
from typing import TYPE_CHECKING

from toolbox import db
from pydantic import BaseModel

from toolbox.mcp_clients.mcp_clients import current_claude_desktop_config, write_claude_desktop_config
from toolbox.mcp_installer.mcp_installer import process_exists
from toolbox.store.store_code import STORE_ELEMENTS
from toolbox.store.store_json import STORE, get_default_setting
from toolbox.utils.healthcheck import HealthStatus, healthcheck
from toolbox.utils.utils import DEFAULT_LOG_FILE, installation_dir_from_name

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext

HOME = Path.home()
INSTALLED_HEADERS = [
    "NAME",
    "CLIENT",
    "DEPLOYMENT",
    "READ ACCESS",
    "WRITE ACCESS",
    "HOST",
    "MANAGED BY",
    "PROXY",
    "VERIFIED",
    "CLIENT CONFIG",
]

HEALTH_STATUS_ICON = {
    HealthStatus.HEALTHY: "🟢",
    HealthStatus.UNHEALTHY: "🔴",
    HealthStatus.UNKNOWN: "🟠",
}


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
            f"{self.name}",
            self.client,
            self.deployment_method,
            ",\n".join(self.read_access),
            ",\n".join(self.write_access),
            self.host,
            f"{self.managed_by} {self.status_icon}",
            self.proxy if self.proxy is not None else "",
            "✓" if self.verified else "",
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
        )
        
    def delete(self, conn: sqlite3.Connection):
        if self.installation_dir.exists():
            shutil.rmtree(self.installation_dir, ignore_errors=True)
        db.db_delete_mcp(conn, self.name)
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
        status_str =  "\n".join([f"{key}: {value}" for key, value in status_dict.items()])
        if status_str == "":
            return ""
        else:
            return f"""
EXTERNAL DEPENDENCY STATUS:
{status_str}
"""
    
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
LOG FILE: {self.log_file}
LOGS:
{logs}
"""

    def show(self):
        print(f"""
========================================
{self.name} {self.status_str}
========================================
{self.external_dependency_check_str()}
{self.logs_str()}
""")
        



def create_clickable_file_link(file_path, link_text="LINK"):
    abs_path = urllib.parse.quote(file_path)
    file_url = f"file://{abs_path}"
    return file_url
