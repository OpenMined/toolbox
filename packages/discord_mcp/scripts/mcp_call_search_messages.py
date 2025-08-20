import asyncio

from fastmcp import Client

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8008/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "search_messages", arguments={"query": "hello", "limit": 5}
        )
        print(f"Search results: {result}")


asyncio.run(main())
