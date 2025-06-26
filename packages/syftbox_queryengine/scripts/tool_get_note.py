from fastmcp import Client
import asyncio

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8002/mcp/mcp")


async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        
        
        meeting_notes = await client.call_tool("get_meeting_content_from_filename",
                                               {"filename": "meeting_2025-06-03 14:30:48.452985+00:00.txt"})
        print(f"Meeting notes: {meeting_notes}")


asyncio.run(main())