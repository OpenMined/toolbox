import contextlib
from contextlib import asynccontextmanager
from threading import Thread

import uvicorn
from fastapi import FastAPI

from discord_mcp.background_worker import (
    run_discord_mesage_download_and_write_background_worker_loop,
)
from discord_mcp.embedding_background_worker import (
    start_embedding_background_worker_embedding,
)
from discord_mcp.mcp_server import mcp


def start_background_worker_download_and_write():
    """Background worker that downloads and writes messages to the database."""
    Thread(
        target=run_discord_mesage_download_and_write_background_worker_loop,
        daemon=True,
    ).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # Start embedding background worker
        print("Starting embedding background worker...")
        embedding_thread = start_embedding_background_worker_embedding()
        print(f"Started embedding background worker: {embedding_thread}")

        # Start background thread that does nothing (original placeholder)
        start_background_worker_download_and_write()

        await stack.enter_async_context(mcp.session_manager.run())
        yield


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=8008)
