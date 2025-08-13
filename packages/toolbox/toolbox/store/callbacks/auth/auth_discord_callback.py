import os
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import requests
from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.settings import settings
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


DISCORD_BASE_URL = "https://discord.com/api/v10"


def request_discord_token():
    print("No DISCORD_TOKEN found in environment, trying other auth methods")
    print(f"""
Go to https://discord.com/ and log in into the *browser* and check the instructions here:
https://github.com/Tyrrrz/DiscordChatExporter/blob/master/.docs/Token-and-IDs.md
""")
    discord_token = input("Enter the token here:")
    return discord_token


def get_discord_guilds(discord_token):
    endpoint = "users/@me/guilds"
    url = f"{DISCORD_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"{discord_token}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://discord.com/channels/@me",
        "Origin": "https://discord.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    params = {"limit": "100", "after": "0"}
    response = requests.get(
        f"{url}?{urlencode(params)}",
        headers=headers,
    )
    guilds = response.json()
    return guilds


def check_connection(discord_token):
    endpoint = "users/@me"
    url = f"{DISCORD_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"{discord_token}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://discord.com/channels/@me",
        "Origin": "https://discord.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Failed to connect to Discord API: {response.status_code} {response.text}"
        )
    return response.json()


def choose_guild_from_list(guilds):
    names = [guild["name"] for guild in guilds]
    names_str = "\n".join([f"- {name}" for i, name in enumerate(names)])
    print(f"Choose a guild from the following list:\n{names_str}")
    guild_name = input("Enter the name of the guild: ")
    matches = [
        guild["name"] for guild in guilds if guild["name"].lower() == guild_name.lower()
    ]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple matches found: {matches}")
        return choose_guild_from_list(matches)
    else:
        print(f"No match found for {guild_name}")
        return choose_guild_from_list(guilds)


def choose_discord_guild(discord_token):
    try:
        discord_guilds = get_discord_guilds(discord_token)
        guild_name = choose_guild_from_list(discord_guilds)
        return guild_name
    except Exception as e:
        print(f"Could not get guilds: {e}")
        return input("Enter the name of the guild: ")


class DiscordAuthCallback(Callback):
    def on_install_init(self, context: "InstallationContext", json_body: dict):
        env = os.environ
        if "DISCORD_TOKEN" in env:
            if settings.use_discord_env_var:
                discord_token = env["DISCORD_TOKEN"]
            else:
                res = input(
                    "Would you like to use the token from the environment? (y/n)"
                )
                if res in ["y", "Y"]:
                    discord_token = env["DISCORD_TOKEN"]
                else:
                    discord_token = request_discord_token()
        else:
            discord_token = request_discord_token()
        context.context_settings["DISCORD_TOKEN"] = discord_token

        check_connection(discord_token)
        guild_name = choose_discord_guild(discord_token)
        context.context_settings["DISCORD_GUILD_NAME"] = guild_name

    def on_run_mcp(self, context: "InstallationContext"):
        from toolbox.store.store_code import STORE_ELEMENTS

        store_element = STORE_ELEMENTS["discord-mcp"]
        install_python_mcp(store_element, context)
