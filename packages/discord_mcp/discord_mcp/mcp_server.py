import logging
import os
import traceback
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from discord_mcp import db
from discord_mcp.models import DiscordMessage, DiscordChannel, DiscordUser
from discord_mcp.embedding_background_worker import get_embedding

DISCORD_MCP_PORT = os.getenv("DISCORD_MCP_PORT", 8008)
mcp = FastMCP("Discord MCP service", stateless_http=True, port=DISCORD_MCP_PORT)

logger = logging.getLogger(__name__)


@mcp.tool()
def get_last_messages_in_my_channels(last_n_days: int = 7) -> dict:
    """Get Discord messages for all channels you are in until last_n_days ago"""
    try:
        with db.get_discord_connection() as conn:
            messages = db.get_messages_from_all_channels(conn, last_n_days)
            return {"messages": [msg.model_dump() for msg in messages]}
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


@mcp.tool()
def get_channels() -> dict:
    """Get all Discord channels. This can be a long list, so if you are looking for a single channel
    or a few channels, use the get_user_id_for_name function."""
    try:
        with db.get_discord_connection() as conn:
            channels = db.get_channels(conn)
            return {"channels": [channel.model_dump() for channel in channels]}
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


@mcp.tool()
def get_users() -> dict:
    """Get all Discord users from the database"""
    try:
        with db.get_discord_connection() as conn:
            users = db.get_users(conn)
            return {"users": [user.model_dump() for user in users]}
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


@mcp.tool()
def get_history(channel_id: str, last_n_days: int = 30) -> dict:
    """Get Discord message history for a channel ID
    
    Args:
        channel_id: The Discord channel ID
        last_n_days: Number of days back to get messages (default 30)
    """
    try:
        with db.get_discord_connection() as conn:
            messages = db.get_messages_from_channel(conn, channel_id, last_n_days)
            return {"messages": [msg.model_dump() for msg in messages]}
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


@mcp.tool()
def get_user_id_for_name(query: str, top_n: int = 5) -> dict:
    """Get user or channel ID for a name using fuzzy matching
    
    Args:
        query: The name to search for
        top_n: Number of top matches to return
    """
    try:
        with db.get_discord_connection() as conn:
            matches = db.get_user_id_for_name(conn, query, top_n)
            return {"matches": matches}
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


@mcp.tool()
def search_messages(query: str, limit: int = 10) -> dict:
    """Search Discord messages using semantic similarity (RAG)
    
    Args:
        query: The search query
        limit: Maximum number of results to return (default 10)
    """
    try:
        with db.get_discord_connection() as conn:
            # Get embedding for the query
            query_embedding = get_embedding(query)
            
            # Find matching chunks
            matching_chunks = db.get_matching_chunks(conn, query_embedding, limit)
            
            # Get full message details for the chunks
            chunks_with_messages = db.get_chunk_messages(conn, matching_chunks)
            
            return {
                "query": query,
                "results": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "chunk_text": chunk["chunk_text"],
                        "messages": [msg.model_dump() for msg in chunk["messages"]]
                    }
                    for chunk in chunks_with_messages
                ]
            }
    except Exception:
        logger.error(traceback.format_exc())
        raise ValueError(traceback.format_exc())


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")