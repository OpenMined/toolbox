from pydantic import BaseModel

from toolbox.store.callbacks.callback import (
    Callback,
    InstallSyftboxQueryengineMCPCallback,
    SyftboxAuthCallback,
    TextInputEnvRequestedSecretCallback,
)


class StoreElement(BaseModel):
    name: str


class NotesMCP(StoreElement):
    name: str = "notes-mcp"
    callbacks: list[Callback] = [SyftboxAuthCallback()]


class SyftboxQueryengineMCP(StoreElement):
    name: str = "syftbox-queryengine-mcp"
    callbacks: list[Callback] = [
        SyftboxAuthCallback(),
        InstallSyftboxQueryengineMCPCallback(),
    ]


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
    "notes-mcp": NotesMCP(),
    "syftbox-queryengine-mcp": SyftboxQueryengineMCP(),
}
