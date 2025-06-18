import base64
import random
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi.responses import HTMLResponse
from fastsyftbox import FastSyftBox
from fastsyftbox.simple_client import DEV_DEFAULT_OWNER_EMAIL, default_dev_data_dir
from syft_core import SyftClientConfig

from data_syncer import db
from data_syncer.models import (
    AudioChunk,
    AudioChunkDB,
    FilesToSyncResponse,
    FileToSync,
    MeetingModel,
    SubmitResult,
    TranscriptionChunksResult,
    TranscriptionStoreRequest,
)
from data_syncer.sync import get_connection, get_files_to_sync, mark_file_as_synced

APP_NAME = "data-syncer"
DEV_MODE = True

if DEV_MODE:
    config = SyftClientConfig(
        client_url=8002,  # random
        path="",  # random
        data_dir=default_dev_data_dir(APP_NAME),
        email=DEV_DEFAULT_OWNER_EMAIL,
    )
else:
    config = SyftClientConfig.load()


app = FastSyftBox(
    app_name="data-syncer",
    syftbox_config=config,
    syftbox_endpoint_tags=[
        "syftbox"
    ],  # endpoints with this tag are also available via Syft RPC
    include_syft_openapi=True,  # Create OpenAPI endpoints for syft-rpc routes
)


# normal fastapi
@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse("<html><body><h1>Welcome to abc</h1>")


@app.post("/get_latest_file_to_sync", tags=["syftbox"])
def get_latest_file_to_sync():
    files: list[AudioChunkDB] = get_files_to_sync(conn)  # noqa: F821
    if len(files) == 0:
        result = FilesToSyncResponse(file=None)
    else:
        file = files[0]
        file_data = Path(file.file_name)
        bts = open(file_data, "rb").read()
        timestamp = datetime.fromtimestamp(file_data.stat().st_mtime)
        file = FileToSync(
            filename=file_data.name,
            chunk_id=file.chunk_id,
            encoded_bts=base64.b64encode(bts).decode("utf-8"),
            timestamp=str(timestamp),
            device="MacBook Pro Microphone",
            user_email=config.email,
        )
        result = FilesToSyncResponse(file=file)
    return result.model_dump_json()


# syft://{datasite}/app_data/{app_name}/rpc/submit_transcription
@app.post("/submit_transcription", tags=["syftbox"])
def submit_transcription(transcription: TranscriptionStoreRequest):
    conn = db.get_db()
    transcription_id = random.randint(0, 1000000)
    db.insert_transcription(
        conn,
        transcription_id=transcription_id,
        audio_chunk_id=transcription.id,
        offset_index=0,
        timestamp=transcription.timestamp,
        transcription=transcription.transcription,
        device=transcription.device,
        is_input_device=True,
        speaker_id=0,
        transcription_engine="deepgram",
        start_time=0,
        end_time=0,
        text_length=len(transcription.transcription),
    )
    mark_file_as_synced(
        conn, AudioChunkDB(file_name=transcription.file_name, chunk_id=transcription.id)
    )

    print("got request", transcription)
    response = SubmitResult(message="success")
    return response.model_dump_json()


@app.post("/query_transcription_chunks", tags=["syftbox"])
def query_transcription_chunks():
    conn = db.get_db()
    transcription_chunks, indexed = db.get_transcription_chunks(conn)

    response = TranscriptionChunksResult(
        transcription_chunks=transcription_chunks, indexed=indexed
    )

    return response.model_dump_json()


@app.post("/submit_meetings", tags=["syftbox"])
def submit_meetings(meetings: list[MeetingModel]):
    conn = db.get_db()

    print("Found", len(meetings), "meetings")
    for meeting in meetings:
        print("Inserting new meeting", meeting.filename)
        db.insert_meeting(conn, meeting.filename, meeting.chunks_ids)


if __name__ == "__main__":
    with get_connection() as conn:
        db.create_tables(conn)
    uvicorn.run(app, host="0.0.0.0", port=8002)
