from typing import TYPE_CHECKING

from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.store.callbacks.auth.auth_slack import do_browser_auth
from toolbox.store.callbacks.auth.auth_slack_keyring import get_tokens_and_cookie
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


def validate_workspace_input(workspaces: list[str]) -> str:
    while True:
        workspace = input("Enter Slack workspace name: ")

        if workspace.lower() in workspaces:
            return workspace
        else:
            print(f"'{workspace}' not found in {workspaces}")


def get_workspace(workspaces: list[str]) -> str:
    print("Found the following Slack workspaces:")
    for workspace in workspaces:
        print(f"- '{workspace}'")
    return validate_workspace_input(workspaces)


def gather_tokens_and_cookie(context: "InstallationContext"):
    tokens_and_cookie = get_tokens_and_cookie()
    workspaces = [x["name"].lower() for x in tokens_and_cookie["tokens"].values()]
    if len(workspaces) == 0:
        raise ValueError("No Slack workspaces found")
    workspace = get_workspace(workspaces)
    slack_token = [
        x["token"]
        for x in tokens_and_cookie["tokens"].values()
        if x["name"].lower() == workspace
    ][0]
    slack_d_cookie = tokens_and_cookie["cookie"]
    return slack_token, slack_d_cookie


class SlackAuthCallback(Callback):
    def on_install_init(self, context: "InstallationContext", json_body: dict):
        try:
            slack_token, slack_d_cookie = gather_tokens_and_cookie(context)
            context.context_settings["SLACK_TOKEN"] = slack_token
            context.context_settings["SLACK_D_COOKIE"] = slack_d_cookie
            return
        except Exception as e:
            print(f"Error getting tokens and cookie: {e}")

            workspace = input("Enter Slack workspace name: ")
            token, d_cookie = do_browser_auth(workspace, "chromium")
            context.context_settings["SLACK_TOKEN"] = token
            context.context_settings["SLACK_D_COOKIE"] = d_cookie

    def on_run_mcp(self, context: "InstallationContext"):
        from toolbox.store.store_code import STORE_ELEMENTS

        store_element = STORE_ELEMENTS["slack-mcp"]
        install_python_mcp(store_element, context)
