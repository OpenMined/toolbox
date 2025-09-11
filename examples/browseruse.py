import asyncio

from browser_use import Agent, ChatAnthropic
from dotenv import load_dotenv

load_dotenv()


async def main():
    agent = Agent(
        task="Go to x.com, then wait until the user has logged in. Once tweets are loaded on the screen print the first 10 tweets.",
        llm=ChatAnthropic(model="claude-sonnet-4-0", temperature=0.0),
    )
    await agent.run()


asyncio.run(main())
