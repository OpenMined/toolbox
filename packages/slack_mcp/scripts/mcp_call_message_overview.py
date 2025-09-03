import asyncio

from fastmcp import Client

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8004/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "get_last_messages_in_my_channels", arguments={"last_n_days": 62}
        )
        print(f"result: {result}")


asyncio.run(main())
