from pathlib import Path
import json
import platform
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from toolbox.installer import MCPConfigItem

HOME = Path.home()


CLAUDE_CONFIG_FILE = (
    f"{HOME}/Library/Application Support/Claude/claude_desktop_config.json"
)


class MCPConfigItem(BaseModel):
    name: str
    json_body: dict
    client: str
    
    
def claude_desktop_installed():
    return Path(CLAUDE_CONFIG_FILE).exists()


MCP_CLIENT_INSTALLATION_CHECKS = {
    "claude": claude_desktop_installed,
}


def check_mcp_client_installation(mcp_client: str):
    if mcp_client not in MCP_CLIENT_INSTALLATION_CHECKS:
        raise ValueError(f"MCP client {mcp_client} not found")
    if not MCP_CLIENT_INSTALLATION_CHECKS[mcp_client]():
        raise ValueError(f"MCP client {mcp_client} not installed")
    
    
def current_claude_desktop_config():
    if platform.system() != "Darwin":
        raise RuntimeError("Currently only macOS is supported")
    with open(
        f"{HOME}/Library/Application Support/Claude/claude_desktop_config.json", "r"
    ) as f:
        return json.load(f)
    
def write_claude_desktop_config(claude_desktop_config: dict):
    with open(
        f"{HOME}/Library/Application Support/Claude/claude_desktop_config.json", "w"
    ) as f:
        json.dump(claude_desktop_config, f, indent=4)


def get_claude_config_items() -> list["MCPConfigItem"]:
    from toolbox.installer import MCPConfigItem
    full_json = current_claude_desktop_config()
    res = []
    for name, json_body in full_json["mcpServers"].items():
        res.append(
            MCPConfigItem(
                name=name,
                json_body=json_body,
                client="claude",
            )
        )
    return res
