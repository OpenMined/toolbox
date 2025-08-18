import asyncio

from fastmcp import Client

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8008/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "get_history",
            arguments={"channel_id": "200000000000000001", "last_n_days": 30},
        )
        print(f"result: {result}")


asyncio.run(main())
