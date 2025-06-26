from fastmcp import Client
import asyncio

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8002/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        meeting_notes_metadata = await client.call_tool("get_meeting_notes_metadata")
        print(f"Meeting notes metadata: {meeting_notes_metadata}")


asyncio.run(main())