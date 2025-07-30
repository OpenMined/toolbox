from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from slack_mcp.remote_server.background_worker import poll_for_chunks_to_index
from slack_mcp.remote_server.server import router
from slack_mcp.remote_server.server_settings import settings

stop_event = threading.Event()


def start_background_workers():
    """Start background workers with optional user authentication."""
    print("Starting meeting indexer")
    indexer_executor = ThreadPoolExecutor(max_workers=3)
    poll_indexer_thread = threading.Thread(
        target=poll_for_chunks_to_index,
        args=(stop_event, indexer_executor),
    )
    poll_indexer_thread.start()

    return (
        poll_indexer_thread,
        indexer_executor,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    poll_indexer_thread, indexer_executor = start_background_workers()
    yield
    indexer_executor.shutdown(wait=False)
    stop_event.set()
    poll_indexer_thread.join(timeout=1)


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    print(f"Settings: {settings}")
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)
