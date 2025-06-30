import base64
import os
import random
import threading
import time
import traceback
from datetime import datetime

import requests
from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db
from notes_mcp.remote_fastapi_server import executor
from notes_mcp.models.audio import TranscriptionStoreRequest
from notes_mcp.models.file import FilesToSyncResponse, FileToSync
from notes_mcp.settings import settings
from notes_mcp.syftbox_client import create_authenticated_client

# file_path = HOME / ".screenpipe" / "data" / "MacBook Pro Microphone (input)_2025-06-03_14-30-45.mp4"
# FILE_PATH = 'path/to/your/audio.wav'  # Local WAV file (16kHz sample rate)
ACTIVITY_THRESHOLD_SECONDS = 10


def add_transcription_to_db(
    conn, bts, audio_chunk_id: int, device: str, timestamp: datetime
):
    transcript = transcribe(bts)
    text_length = len(transcript)
    # TODO: FIX
    # start_time and end_time are not set
    # offset_index is not set
    # speaker_id is not set
    # timestamp is not set
    transcription_id = random.randint(0, 1000000)
    db.insert_transcription(
        conn,
        transcription_id=transcription_id,
        audio_chunk_id=audio_chunk_id,
        offset_index=0,
        timestamp=timestamp,
        transcription=transcript,
        device=device,
        is_input_device=True,
        speaker_id=0,
        transcription_engine="deepgram",
        start_time=0,
        end_time=0,
        text_length=text_length,
    )


def poll_for_new_audio_chunks(stop_event: threading.Event):
    while not stop_event.is_set():
        with db.get_notes_db() as conn:
            users = db.get_users(conn)
            for user in users:
                if db.active_since(conn, user.email, ACTIVITY_THRESHOLD_SECONDS):
                    print("Polling for new audio chunks for user", user.email)
                    executor.submit(
                        _poll_for_new_audio_chunks, user.email, user.access_token
                    )
                else:
                    print(
                        f"User {user.email} has not been active for {ACTIVITY_THRESHOLD_SECONDS} seconds, skipping"
                    )
            if len(users) == 0:
                print("No users found to transcribe")
            time.sleep(10)
    print("DONE")


def _poll_for_new_audio_chunks(email: str, access_token: str):
    client = create_authenticated_client(
        app_name="data-syncer",
        user_email=email,
        access_token=access_token,
    )
    print("Polling for new audio chunks")
    try:
        result = client.post("get_latest_file_to_sync/")
        result.raise_for_status()
        file = FilesToSyncResponse.model_validate_json(result.json()).file
        if file is not None:
            print("Got file to transcribe and upload", file)
            bts = base64.b64decode(file.encoded_bts)
            transcript = transcribe(bts)
            print("transcription succesful, uploading to data-syncer")
            upload_transcription_to_queryengine(client, transcript, file)
        else:
            print("No files to transcribe")

    except Exception:
        print(
            f"Failed calling {client.app_name} on {client.app_owner}/get_latest_file_to_sync: {traceback.format_exc()}"
        )

    time.sleep(10)


def upload_transcription_to_queryengine(
    client: SimpleRPCClient, transcription: str, file: FileToSync
):
    # Prepare the payload for the query engine API
    transcription_request = TranscriptionStoreRequest(
        transcription=transcription,
        audio_chunk_id=file.chunk_id,
        timestamp=file.timestamp,
        user_email=file.user_email,
        device=file.device,
    )

    res = client.post("/submit_transcription", json=transcription_request.model_dump())
    print("sucesffully uploaded to data-syncer")
    res.raise_for_status()


def transcribe(bytes_data: bytes):
    if settings.use_mock_transcription:
        print("using test transcription")
        return "This is a test transcription"

    response = requests.post(
        "https://api.deepgram.com/v1/listen",
        headers={
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "audio/wav",
        },
        params={"model": "nova-2", "smart_format": "true", "sample_rate": "16000"},
        data=bytes_data,
    )
    res = response.json()
    transcript = res["results"]["channels"][0]["alternatives"][0]["transcript"]
    return transcript
