import base64
import random
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastsyftbox import FastSyftBox
from fastsyftbox.simple_client import DEV_DEFAULT_OWNER_EMAIL, default_dev_data_dir
from pydantic import BaseModel
from syft_core import SyftClientConfig

from syftbox_queryengine import db
from syftbox_queryengine.auth import authenticate
from syftbox_queryengine.db import (
    get_query_engine_connection,
    get_screenpipe_connection,
    mark_file_as_synced,
    upsert_heartbeat_entry,
)
from syftbox_queryengine.heartbeat import send_heartbeat
from syftbox_queryengine.models import (
    AudioChunkDB,
    FilesToSyncResponse,
    FileToSync,
    MeetingModel,
    SubmitResult,
    TranscriptionChunksResult,
    TranscriptionStoreRequest,
)
from syftbox_queryengine.settings import settings
from syftbox_queryengine.sync import get_files_to_sync

APP_NAME = "data-syncer"


print("settings.dev_mode", settings.dev_mode)
if settings.dev_mode:
    config = SyftClientConfig(
        client_url=8002,  # random
        path="",  # random
        data_dir=default_dev_data_dir(APP_NAME),
        email=DEV_DEFAULT_OWNER_EMAIL,
    )
else:
    config = SyftClientConfig.load()

print("config", config)


router = APIRouter()


# normal fastapi
@router.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse("<html><body><h1>Welcome to abc</h1>")


# normal fastapi
@router.post("/healthcheck")
def healthcheck():
    return {"status": "ok"}


class RegisterAppHealthcheckRequest(BaseModel):
    app_name: str
    email: str
    url: str


class AppHeartbeatRequest(BaseModel):
    app_name: str


@router.post("/register_app_healthcheck")
def register_app_healthcheck(request: RegisterAppHealthcheckRequest):
    with get_query_engine_connection() as conn:
        send_heartbeat(request.app_name, request.email, request.url)
        upsert_heartbeat_entry(conn, request.app_name, request.email, request.url, True)


@router.post("/app_heartbeat_healthy")
def app_healthcheck(request: AppHeartbeatRequest):
    with get_query_engine_connection() as conn:
        healthy = db.is_healthy(conn, request.app_name)
        if healthy is None:
            return HTTPException(status_code=400, detail="App not found")
        return healthy


@router.post("/get_transcriptions")
def get_transcriptions():
    with get_screenpipe_connection() as conn:
        transcriptions = db.get_all_meeting_notes(conn)
        res = [dict(transcription) for transcription in transcriptions]
        return res


@router.post("/get_latest_file_to_sync", tags=["syftbox"])
def get_latest_file_to_sync(current_user_email: str = Depends(authenticate)):
    with get_query_engine_connection() as conn:
        audio_chunks: list[AudioChunkDB] = get_files_to_sync(conn)  # noqa: F821
        if len(audio_chunks) == 0:
            result = FilesToSyncResponse(file=None)
        else:
            audio_chunk = audio_chunks[0]
            file_data = Path(audio_chunk.file_path)
            bts = open(file_data, "rb").read()
            timestamp = datetime.fromtimestamp(file_data.stat().st_mtime)
            print("timestamp", timestamp)
            audio_chunk = FileToSync(
                filename=file_data.name,
                chunk_id=audio_chunk.chunk_id,
                encoded_bts=base64.b64encode(bts).decode("utf-8"),
                timestamp=str(timestamp),
                device="MacBook Pro Microphone",
                user_email=config.email,
            )
            result = FilesToSyncResponse(file=audio_chunk)
        return result.model_dump_json()


# syft://{datasite}/app_data/{app_name}/rpc/submit_transcription
@router.post("/submit_transcription", tags=["syftbox"])
def submit_transcription(
    transcription_req: TranscriptionStoreRequest,
    current_user_email: str = Depends(authenticate),
):
    with get_screenpipe_connection() as conn:
        transcription_id = random.randint(0, 1000000)
        db.insert_transcription(
            conn,
            transcription_id=transcription_id,
            audio_chunk_id=transcription_req.audio_chunk_id,
            offset_index=0,
            timestamp=transcription_req.timestamp,
            transcription=transcription_req.transcription,
            device=transcription_req.device,
            is_input_device=True,
            speaker_id=0,
            transcription_engine="deepgram",
            start_time=0,
            end_time=0,
            text_length=len(transcription_req.transcription),
        )
        audio_chunk = db.get_audio_chunk_by_id(conn, transcription_req.audio_chunk_id)

    with get_query_engine_connection() as conn:
        mark_file_as_synced(conn, audio_chunk)

        response = SubmitResult(message="success")
        return response.model_dump_json()


@router.post("/query_transcription_chunks", tags=["syftbox"])
def query_transcription_chunks(
    current_user_email: str = Depends(authenticate),
):
    with get_screenpipe_connection() as conn:
        transcription_chunks, indexed = db.get_transcription_chunks(conn)
    print("transcription_chunks", transcription_chunks[0])
    response = TranscriptionChunksResult(
        transcription_chunks=transcription_chunks, indexed=indexed
    )

    return response.model_dump_json()


@router.post("/submit_meetings", tags=["syftbox"])
def submit_meetings(
    meetings: list[MeetingModel],
    current_user_email: str = Depends(authenticate),
):
    with get_screenpipe_connection() as conn:
        print("Found", len(meetings), "meetings")
        for meeting in meetings:
            print("Inserting new meeting", meeting.filename)
            db.insert_meeting(conn, meeting.filename, meeting.chunks_ids)


app = FastSyftBox(
    app_name="data-syncer",
    syftbox_config=config,
    syftbox_endpoint_tags=[
        "syftbox"
    ],  # endpoints with this tag are also available via Syft RPC
    include_syft_openapi=True,  # Create OpenAPI endpoints for syft-rpc routes
)
app.include_router(router)
app.enable_debug_tool(
    endpoint="/get_latest_file_to_sync",
    example_request=str({}),
    publish=True,
)


if __name__ == "__main__":
    with get_query_engine_connection() as conn:
        db.create_queryengine_tables(conn)
    uvicorn.run(app, host="0.0.0.0", port=8002)
