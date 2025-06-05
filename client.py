from fastmcp import Client
import asyncio

# The Client automatically uses StreamableHttpTransport for HTTP URLs
client = Client("http://127.0.0.1:8000/mcp")

async def main():
    async with client:
        # tools = await client.list_tools()
        # print(f"Available tools: {tools}")
        weather_amsterdam = await client.call_tool("get_weather", arguments={"city": "Amsterdam"})
        print(f"Weather in Amsterdam: {weather_amsterdam}")

asyncio.run(main())