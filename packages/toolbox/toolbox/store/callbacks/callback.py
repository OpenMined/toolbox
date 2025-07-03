from __future__ import annotations

import os
import sqlite3
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from pydantic import BaseModel

if TYPE_CHECKING:
    from toolbox.installed_mcp import InstalledMCP
import time
from time import sleep

from toolbox.external_dependencies.external_depenencies import (
    screenpipe_installed,
    syftbox_installed,
    syftbox_running,
)
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
from toolbox.settings import settings

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

    def on_delete(self, mcp: "InstalledMCP"):
        pass

    def on_data_stats(self, mcp: "InstalledMCP"):
        pass


class RequestedSecret(BaseModel):
    result_name: str


class DeleteNotesMCPCallback(Callback):
    def on_delete(self, mcp: "InstalledMCP"):
        db_path = HOME / ".meeting-notes-mcp" / "db.sqlite"
        screenpipe_db_path = HOME / ".screenpipe" / "db.sqlite"
        if db_path.exists():
            print(f"Deleting {db_path}")
            db_path.unlink()
        if screenpipe_db_path.exists():
            conn = sqlite3.connect(screenpipe_db_path)
            cursor = conn.cursor()
            print("Deleting table meeting_meta from screenpipe")
            cursor.execute("DELETE FROM meeting_meta")
            print("Deleting table meeting_audio_chunks from screenpipe")
            cursor.execute("DELETE FROM meeting_audio_chunks")
            print(
                "Deleting audio_transcriptions from screenpipe where transcription_engine='syftbox-whisper-v3-large'"
            )
            cursor.execute(
                "DELETE FROM audio_transcriptions where transcription_engine='syftbox-whisper-v3-large'"
            )
            conn.commit()
            conn.close()


class DeleteSyftboxQueryengineMCPCallback(Callback):
    def on_delete(self, mcp: "InstalledMCP"):
        db_path = HOME / ".query-engine-mcp" / "data.db"
        if db_path.exists():
            print(f"Deleting {db_path}")
            db_path.unlink()


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


class MeetingNotesMCPDataStatsCallback(Callback):
    def on_data_stats(self, mcp: "InstalledMCP") -> dict:
        try:
            query_engine_port = mcp.settings.get("SYFTBOX_QUERYENGINE_PORT", None)
            if query_engine_port is None:
                query_engine_port = mcp.settings.get("syftbox_queryengine_port", None)
                if query_engine_port is None:
                    raise ValueError("SYFTBOX_QUERYENGINE_PORT not found in settings")
            response = requests.post(
                f"http://localhost:{query_engine_port}/get_meeting_transcriptions"
            )
            response.raise_for_status()
            transcriptions = response.json()
            return {
                "meeting_transcriptions": len(transcriptions),
                "db_path": str(HOME / ".screenpipe" / "db.sqlite"),
            }
        except Exception as e:
            return {"error": str(e)}


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
            print("Found existing syftbox email and access token")

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
        # Check if the uvicorn server is already running
        max_retries = 3
        retry_delay = 2  # seconds
        if "SYFTBOX_QUERYENGINE_PORT" not in context.context_settings:
            raise Exception(
                "SYFTBOX_QUERYENGINE_PORT not found in context.context_settings"
            )

        port = context.context_settings["SYFTBOX_QUERYENGINE_PORT"]
        queryengine_url = f"http://localhost:{port}"
        notes_mcp_url = context.context_settings["notes_webserver_url"]
        # first wait until ready
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{queryengine_url}/healthcheck", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise Exception(
                        f"Server not available after {max_retries} attempts"
                    )

        try:
            response = requests.post(
                f"{queryengine_url}/register_app_healthcheck",
                json={
                    "app_name": "notes_mcp",
                    "email": context.context_dict["syftbox_email"],
                    "url": notes_mcp_url,
                },
            )
            response.raise_for_status()
        except Exception as e:
            raise Exception(
                f"Error registering user for NotesMCP, could not connect to {queryengine_url}/register_app_healthcheck {e} {traceback.format_exc()}"
            ) from e


class InstallSyftboxQueryengineMCPCallback(Callback):
    def on_install_init_finished(self, context: InstallationContext):
        mcp = context.mcp
        mcp.settings["syftbox_queryengine_port"] = "8002"
        context.context_settings["SYFTBOX_QUERYENGINE_PORT"] = "8002"

        print("Install syftbox-queryengine-mcp")
        check_uv_installed()
        installation_dir = make_mcp_installation_dir(context.current_app)
        init_venv_uv(installation_dir)

        if settings.use_local_packages:
            # print("\nUsing local packages!!!!\n")
            # TODO: read from configuration
            install_package_from_local_path(
                installation_dir,
                "~/workspace/agentic-syftbox/packages/syftbox_queryengine",
            )
        else:
            # print("\n\n\nUsing remote packages!!!!\n\n\n")
            install_package_from_git(
                installation_dir,
                package_url="https://github.com/OpenMined/agentic-syftbox",
                subdirectory="packages/syftbox_queryengine",
                branch="main",
            )

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
