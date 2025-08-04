from typing import TYPE_CHECKING

from slack_sdk import WebClient
from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.store.callbacks.auth.auth_slack import do_browser_auth
from toolbox.store.callbacks.auth.auth_slack_keyring import (
    get_slack_d_cookie_and_test_with_token,
    get_tokens,
    get_tokens_and_cookie,
)
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


def user_choose_workspace(workspaces: list[str]) -> str:
    print("Found the following Slack workspaces:")
    for workspace in workspaces:
        print(f"- '{workspace}'")
    return validate_workspace_input(workspaces)


def gather_tokens_and_cookie(context: "InstallationContext"):
    tokens = get_tokens()

    workspaces = [x["name"].lower() for x in tokens.values()]
    if len(workspaces) == 0:
        raise ValueError("No Slack workspaces found")
    workspace = user_choose_workspace(workspaces)
    slack_token = [
        x["token"] for x in tokens.values() if x["name"].lower() == workspace
    ][0]

    slack_d_cookie = get_slack_d_cookie_and_test_with_token(slack_token)

    return slack_token, slack_d_cookie


def user_choose_manual_input_or_playwright_auth(workspace):
    prompt = """You can choose to either:
1) manually input your Slack token and cookie from instructions
2) use playwright to authenticate (requires oauth from scratch)
Choose 1 or 2: """
    if input(prompt).lower() == "1":
        print(f"""
Go to https://{workspace}.slack.com
Run the following code in console:
console.log(JSON.parse(localStorage.localConfig_v2).teams[document.location.pathname.match(/^\/client\/([A-Z0-9]+)/)[1]].token)
and paste the result here
""")
        slack_token = input("Enter Slack token: ")
        print(f"""
We also need the d cookie, got to https://{workspace}.slack.com. In your browser go to Application -> Cookies -> https://app.slack.com,
and copy the value of the d cookie.
    """)
        slack_d_cookie = input("Enter Slack d cookie: ")
        return slack_token, slack_d_cookie
    else:
        print("Using playwright to authenticate")
        return do_browser_auth(workspace, "chromium")


class SlackAuthCallback(Callback):
    def on_install_init(self, context: "InstallationContext", json_body: dict):
        try:
            slack_token, slack_d_cookie = gather_tokens_and_cookie(context)
            context.context_settings["SLACK_TOKEN"] = slack_token
            context.context_settings["SLACK_D_COOKIE"] = slack_d_cookie
            raise Exception("Authentication successful")
        except Exception as e:
            print(
                "Failed to read slack cookie from keychain, trying other auth methods"
            )
            workspace = input("Enter Slack workspace name: ")
            slack_token, slack_d_cookie = user_choose_manual_input_or_playwright_auth(
                workspace
            )

            context.context_settings["SLACK_TOKEN"] = slack_token
            context.context_settings["SLACK_D_COOKIE"] = slack_d_cookie

        headers = {
            "Cookie": f"d={slack_d_cookie}",
            "User-Agent": "Mozilla/5.0 (compatible; Python)",
        }
        client = WebClient(token=slack_token, headers=headers)
        response = client.auth_test()
        if response.data["ok"]:
            print("Authentication successful")
        else:
            raise Exception("Authentication failed")

    def on_run_mcp(self, context: "InstallationContext"):
        from toolbox.store.store_code import STORE_ELEMENTS

        store_element = STORE_ELEMENTS["slack-mcp"]
        install_python_mcp(store_element, context)
