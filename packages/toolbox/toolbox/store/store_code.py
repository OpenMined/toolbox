from pydantic import BaseModel

from toolbox.store.callbacks.callback import (
    Callback,
    TextInputEnvRequestedSecretCallback,
)


class StoreElement(BaseModel):
    name: str


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
}
