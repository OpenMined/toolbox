import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import contextlib
import sqlite3
import threading
from typing import Annotated
from notes_mcp import PROJECT_ROOT
from notes_mcp.background_workers.transcriber import add_transcription_to_db
from notes_mcp.db import get_db, insert_audio_chunk
from fastapi import Depends, FastAPI
from pydantic import BaseModel
import uvicorn

from notes_mcp.mcp_server import mcp
from contextlib import asynccontextmanager


BASE_DATA_DIR = PROJECT_ROOT / "data"
N_WORKERS = 2


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        from notes_mcp.background_workers.meeting_indexer import poll_for_new_meetings
        from notes_mcp.fastapi_server import executor
        from notes_mcp.background_workers.meeting_indexer import stop_event as meeting_indexer_stop_event
        await stack.enter_async_context(mcp.session_manager.run())
        print("Starting meeting indexer")
        poll_meetings_producer = threading.Thread(target=poll_for_new_meetings)
        poll_meetings_producer.start()
        yield
        print("Cleaning up exeecutor")
        executor.shutdown(wait=False)
        meeting_indexer_stop_event.set()
        poll_meetings_producer.join(timeout=1)

app = FastAPI(lifespan=lifespan)


executor = ThreadPoolExecutor(max_workers=N_WORKERS)

class AudioRequest(BaseModel):
    file_name: str
    encoded_bts: str
    id: int
    timestamp: str
    user_email: str
    device: str = "MacBook Pro Microphone"


@app.post("/upload_audio_chunk")
def upload_audio_chunk(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    request: AudioRequest
    ):
    file_name = request.file_name
    bts = base64.b64decode(request.encoded_bts)
    chunk_id = request.id
    timestamp = request.timestamp
    user_email = request.user_email
    device = request.device
    
    # relative_path = file_name.split(".screenpipe", 1)[1]
    out_path = (BASE_DATA_DIR / user_email / file_name)
    insert_audio_chunk(conn, chunk_id, out_path.as_posix(), timestamp, user_email)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(bts)    
    
    # todo, do this in background thread
    add_transcription_to_db(conn, bts, chunk_id, device, timestamp)
    return {"message": "Success"}



if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)