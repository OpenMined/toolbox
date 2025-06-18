import base64
import contextlib
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI
from fastsyftbox.simple_client import SimpleRPCClient
from pydantic import BaseModel

from notes_mcp import PROJECT_ROOT
from notes_mcp.background_workers.transcriber import transcribe
from notes_mcp.db import get_db, insert_audio_chunk
from notes_mcp.mcp_server import mcp

BASE_DATA_DIR = PROJECT_ROOT / "data"
N_WORKERS = 2


app = FastAPI()


executor = ThreadPoolExecutor(max_workers=N_WORKERS)


class AudioRequest(BaseModel):
    encoded_bts: str
    audio_chunk_id: int
    timestamp: str
    user_email: str
    device: str = "MacBook Pro Microphone"


# @app.post("/upload_audio_chunk")
# def upload_audio_chunk(request: AudioRequest):
#     bts = base64.b64decode(request.encoded_bts)

#     transcript = transcribe(bts)

#     client = SimpleRPCClient(app_name="data-syncer", dev_mode=True)

#     # Prepare the payload for the data_syncer API
#     payload = {
#         "transcription": transcript,  # No transcription yet, just the audio chunk info
#         "id": request.audio_chunk_id,
#         "timestamp": request.timestamp,
#         "user_email": request.user_email,
#         "device": request.device,
#     }

#     # Optionally, you could send the audio bytes as well, but the data_syncer expects transcription text
#     # So here we just register the chunk metadata for now
#     try:
#         res = client.post("/submit_transcription", json=payload)
#         res.raise_for_status()
#         return {"message": "Success", "data_syncer_response": res.json()}
#     except Exception as e:
#         return {"message": "Failed to submit to data_syncer", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
