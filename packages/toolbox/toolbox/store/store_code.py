from pydantic import BaseModel
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from toolbox.installed_mcp import InstalledMCP
from toolbox.store.callbacks.callback import (
    Callback,
    DeleteNotesMCPCallback,
    DeleteSyftboxQueryengineMCPCallback,
    InstallSyftboxQueryengineMCPCallback,
    MeetingNotesMCPDataStatsCallback,
    RegisterNotesMCPCallback,
    RegisterNotesMCPAppHeartbeatMCPCallback,
    ScreenpipeExternalDependencyCallback,
    SyftboxAuthCallback,
    SyftboxExternalDependencyCallback,
    TextInputEnvRequestedSecretCallback,
)


class StoreElement(BaseModel):
    name: str

    def healthcheck(self) -> bool:
        raise NotImplementedError("Healthcheck not implemented")


class NotesMCP(StoreElement):
    name: str = "meeting-notes-mcp"
    callbacks: list[Callback] = [
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
        print(url)
        res = requests.post(f"{url}/healthcheck")
        # print(res.content)
        return res.json()["status"] == "ok"


class SyftboxQueryengineMCP(StoreElement):
    name: str = "syftbox-queryengine-mcp"
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


class GithubMCP(StoreElement):
    name: str = "github-mcp"
    callbacks: list[Callback] = [
        TextInputEnvRequestedSecretCallback(
            result_name="GITHUB_PERSONAL_ACCESS_TOKEN",
            request_text="To install github mcp, you need a personal access token. Please visit https://github.com/settings/personal-access-tokens to create one.",
        )
    ]


# TODO: make generic
STORE_ELEMENTS = {
    "github-mcp": GithubMCP(),
    "meeting-notes-mcp": NotesMCP(),
    "syftbox-queryengine-mcp": SyftboxQueryengineMCP(),
}
