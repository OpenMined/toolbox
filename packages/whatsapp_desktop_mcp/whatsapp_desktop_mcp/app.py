import contextlib
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import FastAPI

from whatsapp_desktop_mcp.mcp_server import mcp


port = os.getenv("WHATSAPP_DESKTOP_MCP_PORT", "8004")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


if __name__ == "__main__":
    app = FastAPI(
        lifespan=lifespan,
    )
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=port)
