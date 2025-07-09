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


def is_claude_installed_macos():
    possible_paths = [
        Path("/Applications/Claude.app"),
        HOME / "Applications/Claude.app",
    ]
    return any(path.exists() for path in possible_paths)


def claude_desktop_installed():
    if platform.system() == "Darwin":
        return is_claude_installed_macos()
    else:
        raise RuntimeError("Currently only macOS is supported")


MCP_CLIENT_INSTALLATION_CHECKS = {
    "claude": claude_desktop_installed,
}

MCP_CLIENT_NOT_EXIST_ERROR_MESSAGES = {
    "claude": "Claude Desktop is not installed. Please install it from https://claude.ai/download",
}


def check_mcp_client_installation(mcp_client: str):
    if mcp_client not in MCP_CLIENT_INSTALLATION_CHECKS:
        raise ValueError(f"MCP client {mcp_client} not found")
    if not MCP_CLIENT_INSTALLATION_CHECKS[mcp_client]():
        raise ValueError(MCP_CLIENT_NOT_EXIST_ERROR_MESSAGES[mcp_client])


def current_claude_desktop_config(load_if_not_exists: bool = True):
    if platform.system() != "Darwin":
        raise RuntimeError("Currently only macOS is supported")
    if Path(CLAUDE_CONFIG_FILE).exists():
        with open(CLAUDE_CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        if load_if_not_exists:
            return {
                "mcpServers": {},
            }
        else:
            raise FileNotFoundError(
                f"Claude config file {CLAUDE_CONFIG_FILE} not found"
            )


def write_claude_desktop_config(claude_desktop_config: dict):
    with open(CLAUDE_CONFIG_FILE, "w") as f:
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
