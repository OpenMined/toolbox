from fastmcp import Client
import asyncio

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://localhost:8003/mcp/mcp")


async def main():
    async with client:
        result = await client.call_tool(
            "rag", arguments={"query": "What is the weather in Tokyo?"}
        )
        print(f"result: {result}")


asyncio.run(main())
