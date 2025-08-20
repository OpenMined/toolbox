import asyncio

from fastmcp import Client

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8003/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "send_message",
            arguments={"channel_id": "D7GH378QG", "message": "Hello, world!"},
        )
        print(f"result: {result}")


asyncio.run(main())
