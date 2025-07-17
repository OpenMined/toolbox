from fastmcp import Client
import asyncio

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8003/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "get_channel_id_for_name", arguments={"query": "koenvanderveen"}
        )
        print(f"result: {result}")


asyncio.run(main())
