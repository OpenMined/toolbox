import asyncio

from fastmcp import Client

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8004/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        result = await client.call_tool(
            "get_messages_by_contact_id",
            arguments={"contact_id": "31623253111@s.whatsapp.net"},
        )
        print(f"result: {result}")


asyncio.run(main())
