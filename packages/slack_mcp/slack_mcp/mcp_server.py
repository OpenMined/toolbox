import os

from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient

mcp = FastMCP("Meeting Notes MCP service", stateless_http=True)


token = os.getenv("SLACK_TOKEN")
d_cookie = os.getenv("SLACK_D_COOKIE")

headers = {"Cookie": f"d={d_cookie}", "User-Agent": "Mozilla/5.0 (compatible; Python)"}
client = WebClient(token=token, headers=headers)


@mcp.tool()
def send_message(receiver_name: str, message: str) -> dict:
    """send a slack message."""
    print("sending message")
    response = client.chat_postMessage(channel="D022YGA1L9Y", text=message)
    response.validate()
    # response = client.chat_postMessage(
    #     channel="D7GH378QG", text="test message from python slack bot"
    # )
    return {"status": "success"}


@mcp.tool()
def get_history(receiver_name: str) -> dict:
    """get slack conversation history."""
    response = client.conversations_history(channel="D01LM1NMJ0J", limit=3)

    res = []
    for message in response["messages"]:
        res.append(
            {
                "text": message["text"],
                "user": "Madhava (we're hiring)",
                "ts": message["ts"],
            }
        )

    return res


if __name__ == "__main__":
    mcp.run(transport="streamable-http", mount_path="/mcp")
