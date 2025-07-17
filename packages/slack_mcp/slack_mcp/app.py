import contextlib
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from slack_mcp.mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


# app.router.lifespan_context = lifespan


if __name__ == "__main__":
    app = FastAPI(
        lifespan=lifespan,
    )
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=8003)
