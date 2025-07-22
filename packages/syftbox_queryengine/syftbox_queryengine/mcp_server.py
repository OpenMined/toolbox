from mcp.server.fastmcp import FastMCP
from syftbox_queryengine import db

import os
from pathlib import Path


# ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
REPO_PATH = Path(os.environ.get("REPO_PATH", "/Users/koen/workspace/toolbox"))
# SCREENPIPE_PATH = REPO_PATH / "data" / "screenpipe" / "db.sqlite"
# print(f"screenpipe path: {SCREENPIPE_PATH}")
# assert ANTHROPIC_KEY is not None and ANTHROPIC_KEY != ""

# Connect to the SQLite database
# conn = sqlite3.connect(SCREENPIPE_PATH)
# conn.row_factory = sqlite3.Row
# client = Anthropic(api_key=ANTHROPIC_KEY)

# Create FastMCP instance
mcp = FastMCP("Meeting Notes MCP service", stateless_http=True)


@mcp.tool()
def get_meeting_notes_metadata() -> list[dict[str, str]]:
    """Get all meeting note files, returns [{"filename": "filenname1", "datetime": "date1"},
    {"filename": "filenname2", "datetime": "datetime2"}, ...].
    When returning meeting note metadata, as a client always make sure to show the metadata to the user so they can see what is going on."""
    # all_meeting_notes: list[str] = get_all_meeting_notes(conn)
    try:
        with db.get_screenpipe_connection() as conn:
            return db.get_meeting_meta(conn)
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return []


@mcp.tool()
def get_meeting_content_from_filename(filename: str) -> str:
    """Get the meeting notes for a given filename."""
    try:
        with db.get_screenpipe_connection() as conn:
            meeting_notes: str = db.get_meeting_notes_by_filename(conn, filename)
            return meeting_notes
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return ""


# @mcp.tool()
# def get_meeting_todos(query: str) -> str:
#     """Get the meeting notes for a given query."""
#     all_meeting_notes: list[str] = get_all_meeting_notes(conn)
#     # TODO: get the right meeting from all meeting_notes
#     meeting_notes = all_meeting_notes[0]
#     todos: str = get_todos(client, meeting_notes)
#     return todos

# @mcp.tool()
# def get_weather(city: str) -> str:
#     """Get weather information for a city."""
#     # Mock weather data - replace with real API call
#     return f"The weather in {city} is sunny with 72°F"


if __name__ == "__main__":
    # For FastMCP 1.0
    mcp.run(transport="streamable-http", mount_path="/mcp")
    # mcp.run(transport="sse", mount_path="/mcp")

    # For latest fastMCP
    # mcp.run(transport="sse", host="127.0.0.1", port=8000, path="/mcp")
    # mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
