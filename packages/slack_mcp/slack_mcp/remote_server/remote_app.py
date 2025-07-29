import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slack_mcp.remote_server.background_worker import poll_for_chunks_to_index
from slack_mcp.remote_server.server import router
from slack_mcp.remote_server.server_settings import settings

stop_event = threading.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=poll_for_chunks_to_index, args=(stop_event,))
    thread.start()
    yield


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan, port=settings.server_port)
    app.include_router(router)
