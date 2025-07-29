import threading
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager

from slack_mcp.remote_server.background_worker import poll_for_chunks_to_index

router = APIRouter()

stop_event = threading.Event()


@router.get("/health")
async def health():
    return {"status": "ok"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=poll_for_chunks_to_index, args=(stop_event,))
    thread.start()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
