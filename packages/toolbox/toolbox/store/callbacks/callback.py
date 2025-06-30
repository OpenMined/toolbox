from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import requests
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from toolbox.installed_mcp import InstalledMCP
from toolbox.external_dependencies.external_depenencies import (
    screenpipe_installed,
    syftbox_installed,
    syftbox_running,
)
from toolbox.settings import settings
from toolbox.mcp_installer.mcp_installer import (
    check_uv_installed,
    init_venv_uv,
    install_package_from_git,
    install_package_from_local_path,
    make_mcp_installation_dir,
    pkill_f,
    process_exists,
    run_python_mcp,
    should_kill_existing_process,
)

HOME = Path.home()

INHERIT_SECRET_FROM_ENV = True
REQUEST_REUSE = False
AUTOMATIC_REUSE = True

from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


class Callback(BaseModel):
    def on_input(self, context: InstallationContext):
        pass

    def on_external_dependency_check(self, context: InstallationContext):
        return {}

    def on_install_init(self, context: InstallationContext, json_body: dict):
        pass

    def on_install_init_finished(self, context: InstallationContext):
        pass

    def on_external_dependency_status_check(self, mcp: "InstalledMCP"):
        pass


class RequestedSecret(BaseModel):
    result_name: str


class TextInputEnvRequestedSecretCallback(RequestedSecret, Callback):
    request_text: str
    value: str | None = None

    def on_input(self, context: InstallationContext):
        if INHERIT_SECRET_FROM_ENV and self.result_name in os.environ:
            print(f"inheriting secret {self.result_name} from env")
            self.value = os.environ[self.result_name]
        else:
            res = input(self.request_text + "\n" + "Enter value:")
            self.value = res

    def on_install_init(self, context: InstallationContext, json_body: dict):
        if "env" not in json_body:
            json_body["env"] = {}
        json_body["env"][self.result_name] = self.value


def request_reuse(key: str) -> bool:
    reuse = input(f"Found existing {key}. Reuse? (y/n)")
    if reuse in ["y", "Y"]:
        return True
    elif reuse in ["n", "N"]:
        return False
    else:
        print("Invalid input. Please enter y or n.")
        return request_reuse(key)


class SyftboxExternalDependencyCallback(Callback):
    def on_external_dependency_check(self, context: InstallationContext):
        if not syftbox_installed():
            input(
                """
Syftbox is not installed. Please install it from https://github.com/OpenMined/syftbox and run it.
Press Enter to continue."""
            )
        elif not syftbox_running():
            input(
                """
Syftbox is not running. Please install it from https://github.com/OpenMined/syftbox and run it.
Press Enter to continue."""
            )

    def on_external_dependency_status_check(self, mcp: "InstalledMCP") -> dict:
        running = syftbox_running()
        installed = syftbox_installed()
        if running:
            return {
                "syftbox": "🟢",
            }
        elif installed:
            return {
                "syftbox": "🟠 (not running)",
            }
        else:
            return {
                "syftbox": "🔴",
            }


class ScreenpipeExternalDependencyCallback(Callback):
    def on_external_dependency_check(self, context: InstallationContext):
        if not screenpipe_installed():
            input(
                """
Screenpipe is not installed. Please run it using `curl -fsSL get.screenpi.pe/cli | sh`. or by using `screenpipe` if already installed
Press Enter to continue."""
            )

    def on_external_dependency_status_check(self, mcp: "InstalledMCP") -> dict:
        installed = screenpipe_installed()
        installed_icon = "🟢" if installed else "🔴"
        return {
            "screenpipe": installed_icon,
        }


class SyftboxAuthCallback(Callback):
    keys: list[str] = ["syftbox_email", "syftbox_access_token"]

    def on_input(self, context: InstallationContext):
        request_email = True
        if "syftbox_email" in context.context_dict:
            if AUTOMATIC_REUSE:
                request_email = False
            if REQUEST_REUSE:
                reuse = request_reuse("syftbox email and access token")
                if reuse:
                    request_email = False

        if request_email:
            email = input("""\nFill in your syftbox email, if you already have one, enter it, if not you can regsiter by
going to http://172.172.234.167:7000/syftbox/login and get your access token (store it).
syftbox email: """)
            # TODO: maybe only have one
            context.context_dict["syftbox_email"] = email
            context.context_settings["SYFTBOX_EMAIL"] = email

            access_token = input("syftbox access token: ")
            context.context_dict["syftbox_access_token"] = access_token
            context.context_settings["SYFTBOX_ACCESS_TOKEN"] = access_token
        else:
            print("Reusing syftbox email and access token")

        if "syftbox_access_token" not in context.context_dict:
            access_token = input("syftbox access token: ")
            context.context_dict["syftbox_access_token"] = access_token
            context.context_settings["SYFTBOX_ACCESS_TOKEN"] = access_token

    def on_install_init(self, context: InstallationContext, json_body: dict):
        if "env" not in json_body:
            json_body["env"] = {}
        for key in self.keys:
            json_body["env"][key] = context.context_dict[key]


class RegisterNotesMCPCallback(Callback):
    def on_install_init(self, context: InstallationContext, json_body: dict):
        payload = {
            "email": context.context_dict["syftbox_email"],
            "access_token": context.context_dict["syftbox_access_token"],
        }
        try:
            url = context.context_settings["notes_webserver_url"]
            response = requests.post(f"{url}/register_user", json=payload)
            response.raise_for_status()
            print(
                f"Succesfully registered account for meeting notes MCP {context.context_dict['syftbox_access_token']}"
            )

        except Exception as e:
            # print(e)
            raise Exception(
                f"Error registering user for NotesMCP, could not connect to {url}"
            ) from e


class RegisterNotesMCPAppHeartbeatMCPCallback(Callback):
    def on_install_init(self, context: InstallationContext, json_body: dict):
        try:
            port = context.context_settings["SYFTBOX_QUERYENGINE_PORT"]
            url = f"http://localhost:{port}"
            response = requests.post(
                f"{url}/register_app_healthcheck",
                json={
                    "app_name": "notes_mcp",
                    "email": context.context_dict["syftbox_email"],
                    "url": url,
                },
            )
            response.raise_for_status()
            print("Succesfully registered app heartbeat for meeting notes MCP ")
        except KeyError:
            raise Exception(
                "Could not find SYFTBOX_QUERYENGINE_PORT in context.context_settings"
            )
        except Exception as e:
            raise Exception(
                f"Error registering user for NotesMCP, could not connect to {url}"
            ) from e


class InstallSyftboxQueryengineMCPCallback(Callback):
    def on_install_init_finished(self, context: InstallationContext):
        mcp = context.mcp
        mcp.settings["syftbox_queryengine_port"] = "8002"
        context.context_settings["SYFTBOX_QUERYENGINE_PORT"] = "8002"

        print("Install syftbox-queryengine-mcp")
        print("Check if uv is installed")
        check_uv_installed()
        print("Make installation directory")
        installation_dir = make_mcp_installation_dir(context.current_app)
        print("Init venv")
        init_venv_uv(installation_dir)
        print("Install syftbox-queryengine-mcp from git")

        if settings.use_local_packages:
            print("\n\n\nUsing local packages!!!!\n\n\n")
            # TODO: read from configuration
            install_package_from_local_path(
                installation_dir,
                "~/workspace/agentic-syftbox/packages/syftbox_queryengine",
            )
        else:
            print("\n\n\nUsing remote packages!!!!\n\n\n")
            install_package_from_git(
                installation_dir,
                package_url="https://github.com/OpenMined/agentic-syftbox",
                subdirectory="packages/syftbox_queryengine",
                branch="main",
            )

        print("Run syftbox_queryengine.app mcp module")

        module = mcp.deployment["module"]
        start_process = True
        if process_exists(module):
            kill_process = should_kill_existing_process(module)
            if kill_process:
                pkill_f(module)
            else:
                start_process = False

        if start_process:
            run_python_mcp(installation_dir, module, env=context.context_settings)
