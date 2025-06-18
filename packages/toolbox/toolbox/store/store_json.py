import platform

DEFAULT_LOCAL_MACHINE_NAME = platform.node()
MANAGED_BY_INHERIT_CLIENT = "INHERIT_CLIENT"


GLOBAL_MCP_DEFAULTS = {
    "default_host": DEFAULT_LOCAL_MACHINE_NAME,
    "default_verified": True,
    "default_proxy": "mcp-remote",
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
        "json_bodies_for_client_for_deployment_method": {
            "all": {
                "proxy-to-om-enclave": {
                    "args": ["mcp-remote", "http://127.0.0.1:8000/mcp"],
                    "command": "npx",
                }
            }
        },
        "default_settings": {
            "default_read_access": ["Apple Audio Recordings"],
            "default_write_access": ["Meeting Notes"],
            "default_model": None,
            "default_proxy": "mcp-remote",
            "default_host": "OM enclave",
            "default_managed_by": "OM enclave",
            "default_deployment_method": "proxy-to-om-enclave",
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
    return name
