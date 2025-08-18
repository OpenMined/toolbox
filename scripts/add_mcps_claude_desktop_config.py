import json
import os
import sys
from pathlib import Path

HOME_DIR = Path.home()
if sys.platform == "darwin":
    CONFIG_PATH = (
        HOME_DIR
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json"
    )
else:
    assert False, "Unsupported platform"
    # CONFIG_PATH = HOME_DIR / ".config" / "claude" / "claude_desktop_config.json"

config = json.loads(CONFIG_PATH.read_text())
GITHUB_PERSONAL_ACCESS_TOKEN = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
MEETING_NOTES_MCP_SERVICE_NAME = "Meeting Notes MCP service"
GITHUB_MCP_SERVER_NAME = "github"

MEETING_NOTES_MCP_CONFIG = {
    "command": "npx",
    "args": ["mcp-remote", "http://127.0.0.1:8000/mcp"],
}

GITHUB_MCP_CONFIG = {
    "command": "docker",
    "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server",
    ],
    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PERSONAL_ACCESS_TOKEN},
}

if GITHUB_PERSONAL_ACCESS_TOKEN is None or GITHUB_PERSONAL_ACCESS_TOKEN == "":
    raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN is not set")

config["mcpServers"] = config.get("mcpServers", {})

if GITHUB_MCP_SERVER_NAME not in config["mcpServers"]:
    config["mcpServers"][GITHUB_MCP_SERVER_NAME] = GITHUB_MCP_CONFIG
else:
    print("Github MCP server already exists, not adding again")

if MEETING_NOTES_MCP_SERVICE_NAME not in config["mcpServers"]:
    config["mcpServers"][MEETING_NOTES_MCP_SERVICE_NAME] = MEETING_NOTES_MCP_CONFIG
else:
    print("Meeting Notes MCP service already exists, not adding again")

CONFIG_PATH.write_text(json.dumps(config, indent=2))
