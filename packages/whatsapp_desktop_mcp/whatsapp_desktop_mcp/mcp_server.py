from mcp.server.fastmcp import FastMCP

from whatsapp_desktop_mcp.models import MultipleChatsResponse
from whatsapp_desktop_mcp.utils import (
    get_chat_id_for_name,
    get_message_by_contact_id,
    get_recent_messages,
)

mcp = FastMCP("Whatsapp MCP service", stateless_http=True)


@mcp.tool()
def get_channel_id_for_name(channel_name_query: str) -> dict:
    """get the channel id for a name **of a channel or user**. on whatsapp"""
    return get_chat_id_for_name(channel_name_query).model_dump_json()


@mcp.tool()
def get_messages_by_contact_id(contact_id: str) -> dict:
    """get the messages for a contact id. on whatsapp"""
    return get_message_by_contact_id(contact_id).model_dump_json()


@mcp.tool()
def get_last_messages_in_chats(n_days_ago: int = 7) -> dict:
    """get whatsapp messages for all channels you are in until last_n_days ago"""
    chats = get_recent_messages(n_days_ago=n_days_ago)
    return MultipleChatsResponse(chats=chats).model_dump_json()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")
