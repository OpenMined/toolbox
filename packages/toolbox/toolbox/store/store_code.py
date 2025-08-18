from pathlib import Path
from typing import TYPE_CHECKING

import requests
from pydantic import BaseModel

from toolbox.store.callbacks.auth.auth_discord_callback import DiscordAuthCallback
from toolbox.store.callbacks.auth.auth_slack_callback import SlackAuthCallback
from toolbox.store.callbacks.pdf_callback import (
    InstallPDFMCPCallback,
    PDFMCPDataStatsCallback,
    PDFMCPExternalDependencyCallback,
    PDFMCPInstallationSummaryCallback,
)
from toolbox.store.callbacks.whatsapp_callback import InstallWhatsappDesktopMCPCallback

if TYPE_CHECKING:
    from toolbox.installed_mcp import InstalledMCP
from toolbox.settings import TOOLBOX_WORKSPACE_DIR
from toolbox.store.callbacks.callback import (
    Callback,
    DeleteNotesMCPCallback,
    DeleteSyftboxQueryengineMCPCallback,
    DiscordMCPDataStatsCallback,
    InstallSyftboxQueryengineMCPCallback,
    MeetingNotesMCPDataStatsCallback,
    NotesMCPInstallationSummaryCallback,
    ObsidianFindVaultCallback,
    RegisterNotesMCPAppHeartbeatMCPCallback,
    RegisterNotesMCPCallback,
    RegisterSlackMCPCallback,
    ScreenpipeExternalDependencyCallback,
    SlackMCPDataStatsCallback,
    SyftboxAuthCallback,
    SyftboxExternalDependencyCallback,
    TextInputEnvRequestedSecretCallback,
)

# PDF MCP callbacks are now imported from pdf_callback.py

WHATSAPP_DESKTOP_SQLITE_DB_PATH = (
    Path(
        "~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
    )
    .expanduser()
    .resolve()
)


class StoreElement(BaseModel):
    name: str
    local_package_path: Path | None = None
    package_url: str | None = None
    subdirectory: str | None = None
    branch: str | None = None

    def healthcheck(self) -> bool:
        raise NotImplementedError("Healthcheck not implemented")


class NotesMCP(StoreElement):
    name: str = "meeting-notes-mcp"
    local_package_path: Path | None = None
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/syftbox_queryengine"
    branch: str = "main"
    callbacks: list[Callback] = [
        NotesMCPInstallationSummaryCallback(),
        SyftboxAuthCallback(),
        RegisterNotesMCPCallback(),
        RegisterNotesMCPAppHeartbeatMCPCallback(),
        ScreenpipeExternalDependencyCallback(),
        SyftboxExternalDependencyCallback(),
        DeleteNotesMCPCallback(),
        MeetingNotesMCPDataStatsCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        url = mcp.settings["notes_webserver_url"]
        res = requests.post(f"{url}/healthcheck")
        # print(res.content)
        return res.json()["status"] == "ok"


class SyftboxQueryengineMCP(StoreElement):
    name: str = "syftbox-queryengine-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/syftbox_queryengine"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/syftbox_queryengine"
    branch: str = "main"
    callbacks: list[Callback] = [
        SyftboxAuthCallback(),
        InstallSyftboxQueryengineMCPCallback(),
        ScreenpipeExternalDependencyCallback(),
        SyftboxExternalDependencyCallback(),
        DeleteSyftboxQueryengineMCPCallback(),
        MeetingNotesMCPDataStatsCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        port = mcp.settings["syftbox_queryengine_port"]
        res = requests.post(f"http://localhost:{port}/healthcheck")
        return res.json()["status"] == "ok"


class SlackMCP(StoreElement):
    name: str = "slack-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/slack_mcp"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/slack_mcp"
    branch: str = "main"
    callbacks: list[Callback] = [
        SlackAuthCallback(),
        RegisterSlackMCPCallback(),
        SlackMCPDataStatsCallback(),
        SyftboxExternalDependencyCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        return True


class DiscordMCP(StoreElement):
    name: str = "discord-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/discord_mcp"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/discord_mcp"
    branch: str = "main"
    callbacks: list[Callback] = [
        DiscordAuthCallback(),
        DiscordMCPDataStatsCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        return True


class WhatsappDesktopMCP(StoreElement):
    name: str = "whatsapp-desktop-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/whatsapp_desktop_mcp"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/whatsapp_desktop_mcp"
    branch: str = "main"
    callbacks: list[Callback] = [
        InstallWhatsappDesktopMCPCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        if not WHATSAPP_DESKTOP_SQLITE_DB_PATH.exists():
            return False
        else:
            return True


class GithubMCP(StoreElement):
    name: str = "github-mcp"
    callbacks: list[Callback] = [
        TextInputEnvRequestedSecretCallback(
            result_name="GITHUB_PERSONAL_ACCESS_TOKEN",
            request_text="To install github mcp, you need a personal access token. Please visit https://github.com/settings/personal-access-tokens to create one.",
        )
    ]


class PDFMCP(StoreElement):
    name: str = "pdf-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/pdf_mcp"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/pdf_mcp"
    branch: str = "main"
    callbacks: list[Callback] = [
        PDFMCPInstallationSummaryCallback(),
        PDFMCPExternalDependencyCallback(),
        InstallPDFMCPCallback(),
        PDFMCPDataStatsCallback(),
    ]

    def healthcheck(self, mcp: "InstalledMCP") -> bool:
        return True


class ObsidianMCP(StoreElement):
    name: str = "obsidian-mcp"
    local_package_path: Path = Path(
        TOOLBOX_WORKSPACE_DIR / "packages/obsidian_mcp"
    ).expanduser()
    package_url: str = "https://github.com/OpenMined/toolbox"
    subdirectory: str = "packages/obsidian_mcp"
    branch: str = "main"

    callbacks: list[Callback] = [
        ObsidianFindVaultCallback(),
    ]


# TODO: make generic
STORE_ELEMENTS = {
    "github-mcp": GithubMCP(),
    "meeting-notes-mcp": NotesMCP(),
    "syftbox-queryengine-mcp": SyftboxQueryengineMCP(),
    "slack-mcp": SlackMCP(),
    "discord-mcp": DiscordMCP(),
    "whatsapp-desktop-mcp": WhatsappDesktopMCP(),
    "pdf-mcp": PDFMCP(),
    "obsidian-mcp": ObsidianMCP(),
}
