import platform

from packages.toolbox.toolbox.store.store_code import STORE_ELEMENTS
from toolbox.settings import settings

DEFAULT_LOCAL_MACHINE_NAME = platform.node()
MANAGED_BY_INHERIT_CLIENT = "INHERIT_CLIENT"


GLOBAL_MCP_DEFAULTS = {
    "default_host": DEFAULT_LOCAL_MACHINE_NAME,
    "default_verified": True,
    "default_proxy": "mcp-remote",
    "default_app_type": "mcp",
}

# you either provide a client and nothing, then it chooses the default deployment of the client, or of all
# or you provide a client and a deployment method then it chooses that deployment method for that client

STORE = {
    "github-mcp": {
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "stdio": {
                    "args": [
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server",
                    ],
                    "command": "docker",
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "<insert-token-here>"},
                },
            }
        },
        "url": "https://github.com/github/github-mcp-server",
        "secret_requests": [
            {
                "request_type": "text_input",
                "result_type": "env",
                "result_name": "GITHUB_PERSONAL_ACCESS_TOKEN",
                "request_text": "To install github mcp, you need a personal access token. Please visit https://github.com/settings/personal-access-tokens to create one.",
            }
        ],
        "default_settings": {
            "default_read_access": ["Issues", "PRs", "Settings"],
            "default_write_access": ["Issues", "PRs", "Settings"],
            "default_model": None,
            "default_proxy": None,
            "default_managed_by": MANAGED_BY_INHERIT_CLIENT,
            "default_deployment_method": "stdio",
        },
    },
    "meeting-notes-mcp": {
        "has_client_json": False,
        "url": "https://github.com/OpenMined/toolbox/tree/main/packages/notes_mcp",
        "requirements": ["syftbox-queryengine-mcp"],
        "external_dependencies": ["syftbox", "screenpipe"],
        "context_settings": {
            "notes_webserver_url": "http://20.224.153.50:8000/",
        },
        "default_settings": {
            "default_read_access": ["Apple Audio Recordings"],
            "default_write_access": ["Meetings", "Transcriptions"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "OM enclave",
            "default_managed_by": "OM enclave",
            "default_deployment_method": "proxy-to-om-enclave",
            "default_app_type": "bg agent",
        },
    },
    "syftbox-queryengine-mcp": {
        "url": "https://github.com/OpenMined/toolbox/tree/main/packages/syftbox_queryengine",
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "proxy-to-local-http": {
                    "args": ["mcp-remote", "http://127.0.0.1:8002/mcp/mcp"],
                    "command": "npx",
                }
            }
        },
        "mcp_deployment_methods": {"all": "infered"},
        "deployment": {
            "type": "python",
            "module": "syftbox_queryengine.app",
        },
        "default_settings": {
            "default_read_access": ["Apple Audio Recordings"],
            "default_write_access": ["Meeting Notes"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "local",
            "default_managed_by": "toolbox (local)",
            "default_deployment_method": "proxy-to-local-http",
        },
    },
    "slack-mcp": {
        "url": "https://github.com/OpenMined/toolbox/tree/main/packages/slack_mcp",
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "proxy-to-local-http": {
                    "args": ["mcp-remote", "http://127.0.0.1:8004/mcp/mcp"],
                    "command": "npx",
                }
            }
        },
        "external_dependencies": ["syftbox"],
        "context_settings": {
            "slack_webserver_url": "http://20.224.153.50:8005/",
        },
        "mcp_deployment_methods": {"all": "infered"},
        "deployment": {
            "type": "python",
            "module": "slack_mcp.app",
        },
        "default_settings": {
            "default_read_access": ["Slack Messages, Channels, Users"],
            "default_write_access": ["Slack Messages, Channels, Users"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "local",
            "default_managed_by": "toolbox (local)",
            "default_deployment_method": "proxy-to-local-http",
        },
    },
    "whatsapp-desktop-mcp": {
        "url": "https://github.com/OpenMined/toolbox/tree/main/packages/whatsapp_desktop_mcp",
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "proxy-to-local-http": {
                    "args": ["mcp-remote", "http://127.0.0.1:8004/mcp/mcp"],
                    "command": "npx",
                }
            }
        },
        "mcp_deployment_methods": {"all": "infered"},
        "deployment": {
            "type": "python",
            "module": "whatsapp_desktop_mcp.app",
        },
        "default_settings": {
            "default_read_access": ["Whatsapp Messages, Channels, Users"],
            "default_write_access": ["Whatsapp Messages, Channels, Users"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "local",
            "default_managed_by": "toolbox (local)",
            "default_deployment_method": "proxy-to-local-http",
        },
    },
    "obsidian-mcp": {
        "url": "https://github.com/OpenMined/toolbox/tree/main/packages/obsidian_mcp",
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "proxy-to-local-http": {
                    "args": ["mcp-remote", "http://127.0.0.1:8007/mcp/mcp"],
                    "command": "npx",
                }
            }
        },
        "mcp_deployment_methods": {"all": "infered"},
        "deployment": {
            "type": "python",
            "module": "obsidian_mcp.app",
        },
        "default_settings": {
            "default_read_access": ["Obsidian Vault Files"],
            "default_write_access": ["Obsidian Vault Files"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "local",
            "default_managed_by": "toolbox (local)",
            "default_deployment_method": "proxy-to-local-http",
        },
    },
}


def get_default_setting(name: str, client: str, key: str):
    MCP_DEFAULTS = STORE[name]["default_settings"]
    default_key = "default_" + key
    if default_key in MCP_DEFAULTS:
        res = MCP_DEFAULTS[default_key]
    else:
        res = GLOBAL_MCP_DEFAULTS[default_key]
    if res == MANAGED_BY_INHERIT_CLIENT:
        res = client
    return res


def check_name(name: str):
    if name not in STORE:
        raise ValueError(f"MCP with name {name} does not exist")
    if name not in STORE_ELEMENTS:
        raise ValueError(f"MCP with name {name} does not exist")
    return name
