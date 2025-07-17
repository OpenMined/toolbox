import logging
import os
import traceback

from mcp.server.fastmcp import FastMCP
from slack_mcp.overview_utils import (
    get_last_week_messages_with_names,
    get_last_week_messages_with_threads_with_names,
    get_my_active_channels_from_search,
)
from slack_sdk import WebClient

from slack_mcp.models import NamesMatchResponse
from slack_mcp.utils import (
    compute_channelid_to_name_cached,
    get_favourite_channel_ids,
    get_matches_for_name,
)

mcp = FastMCP("Slack MCP service", stateless_http=True)


token = os.getenv("SLACK_TOKEN")
d_cookie = os.getenv("SLACK_D_COOKIE")

headers = {"Cookie": f"d={d_cookie}", "User-Agent": "Mozilla/5.0 (compatible; Python)"}
client = WebClient(token=token, headers=headers)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_channel_id_for_name(query: str) -> dict:
    """get the channel id for a name **of a channel or user**. on slack"""
    try:
        favourite_channel_ids = get_favourite_channel_ids(client)
        channel_to_name, _ = compute_channelid_to_name_cached(client)
        favourite_names = [channel_to_name[x] for x in favourite_channel_ids]
        name2channelid = {v: k for k, v in channel_to_name.items()}
        all_names = list(name2channelid.keys())
        result: NamesMatchResponse = get_matches_for_name(
            query, favourite_names, all_names, name2channelid
        )
        res = result.model_dump_json()
    except Exception:
        raise ValueError(traceback.format_exc())

    return res


@mcp.tool()
def get_channels() -> dict:
    """get all channels on slack. This is can be a long list, so if you are looking for a single channel
    or a few channels, use the get_channel_id_for_name tool."""
    response = client.conversations_list()
    return response["channels"]


@mcp.tool()
def send_message(channel_id: str, message: str) -> dict:
    """send a slack message to a channel id, channel id can be for a channel or user"""
    response = client.chat_postMessage(channel=channel_id, text=message)
    response.validate()
    return {"status": "success"}


@mcp.tool()
def get_last_messages_in_my_channels(last_n_days: int = 7) -> dict:
    """get slack messages for all channels you are in until last_n_days ago"""
    channel_ids = get_my_active_channels_from_search(client, last_n_days=last_n_days)
    channelid_to_name, user_id_to_real_name = compute_channelid_to_name_cached(client)

    messages_by_channel = get_last_week_messages_with_threads_with_names(
        client, channel_ids, channelid_to_name, user_id_to_real_name
    )
    return messages_by_channel


@mcp.tool()
def get_history(
    channel_id: str,
    oldest: str | None = None,
    latest: str | None = None,
    inclusive: bool = False,
    limit: int = 30,
) -> dict:
    """get slack conversation history for a channel id, channel id can be for a channel or user
    oldest: Only messages after this Unix timestamp will be included in results.
    latest: Only messages before this Unix timestamp will be included in results.
    inclusive: Whether to include messages with the oldest or latest timestamp in the results.
    limit: The maximum number of messages to return.

    if both oldest and latest are provided, only messages between the two timestamps will be included in results.
    if only oldest is provided, only messages after the timestamp will be included in results.
    if only latest is provided, only messages before the timestamp will be included in results.

    if neither oldest nor latest is provided, all messages will be included in results.

    """
    response = client.conversations_history(
        channel=channel_id,
        limit=limit,
        oldest=oldest,
        latest=latest,
        inclusive=inclusive,
    )
    channel_to_name, user_id_to_real_name = compute_channelid_to_name_cached(client)
    res = []
    for message in response["messages"]:
        user_name = user_id_to_real_name.get(
            message.get("user", "unknown"), "Unknown User"
        )
        message["user_name"] = user_name
        res.append(message)

    return res


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")
