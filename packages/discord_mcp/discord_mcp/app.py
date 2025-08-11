import contextlib
from contextlib import asynccontextmanager
from threading import Thread

import uvicorn
from fastapi import FastAPI

from discord_mcp.mcp_server import mcp


def background_worker_loop():
    """Background worker that does nothing (placeholder)."""
    import time
    while True:
        print("Background worker running...")
        time.sleep(60)  # Sleep for 1 minute


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # Start background thread that does nothing
        thread = Thread(target=background_worker_loop, daemon=True)
        thread.start()
        await stack.enter_async_context(mcp.session_manager.run())
        yield


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=8008)