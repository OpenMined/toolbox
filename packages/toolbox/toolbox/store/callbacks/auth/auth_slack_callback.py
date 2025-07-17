from typing import TYPE_CHECKING

from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.store.callbacks.auth.auth_slack import do_auth
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


class SlackAuthCallback(Callback):
    def on_install_init(self, context: "InstallationContext", json_body: dict):
        workspace = input("Enter Slack workspace name: ")
        token, d_cookie = do_auth(workspace, "chromium")
        context.context_settings["slack_token"] = token
        context.context_settings["slack_d_cookie"] = d_cookie

    def on_run_mcp(self, context: "InstallationContext"):
        from toolbox.store.store_code import STORE_ELEMENTS

        store_element = STORE_ELEMENTS["slack-mcp"]
        install_python_mcp(store_element, context)
