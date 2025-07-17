from typing import TYPE_CHECKING

from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.settings import settings
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


class InstallWhatsappDesktopMCPCallback(Callback):
    def on_run_mcp(self, context: "InstallationContext"):
        mcp = context.mcp
        mcp.settings["whatsapp_desktop_mcp_port"] = "8004"
        context.context_settings["WHATSAPP_DESKTOP_MCP_PORT"] = "8004"

        print("Install whatsapp-desktop-mcp")
        if settings.do_whatsapp_desktop_check:
            input(
                "Please install whatsapp from https://www.whatsapp.com/download and then press enter"
            )
        from toolbox.store.store_code import STORE_ELEMENTS

        store_element = STORE_ELEMENTS["whatsapp-desktop-mcp"]
        install_python_mcp(store_element, context)
