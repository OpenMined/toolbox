import base64
import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import httpx
import requests
from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db
from notes_mcp.background_workers.user_polling_manager import UserPollingManager
from notes_mcp.models.audio import TranscribeRequest, TranscriptionStoreRequest
from notes_mcp.models.file import FilesToSyncResponse, FileToSync
from notes_mcp.settings import settings
from notes_mcp.syftbox_client import create_authenticated_client

# file_path = HOME / ".screenpipe" / "data" / "MacBook Pro Microphone (input)_2025-06-03_14-30-45.mp4"
# FILE_PATH = 'path/to/your/audio.wav'  # Local WAV file (16kHz sample rate)
ACTIVITY_THRESHOLD_SECONDS = 10
AUDIO_CHUNK_POLL_INTERVAL = 1


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


def poll_for_new_audio_chunks(
    stop_event: threading.Event, executor: ThreadPoolExecutor
):
    polling_manager = UserPollingManager(executor)
    while not stop_event.is_set():
        with db.get_notes_db() as conn:
            users = db.get_users(conn)
            users_already_processed = set()
            users_inactive = set()
            for user in users:
                if db.active_since(conn, user.email, ACTIVITY_THRESHOLD_SECONDS):
                    future = polling_manager.submit_job(
                        user.id, _poll_for_new_audio_chunks, (user.id,)
                    )
                    if future is not None:
                        print(f"Polling for new audio chunks for user {user.email}")
                    else:
                        users_already_processed.add(user.email)
                else:
                    users_inactive.add(user.email)
            if len(users) == 0:
                print("No users found to transcribe")
            time.sleep(AUDIO_CHUNK_POLL_INTERVAL)

    # Shutdown the polling manager when the main polling loop stops
    polling_manager.shutdown()
    print("DONE")


def _poll_for_new_audio_chunks(user_id: int):
    with db.get_notes_db() as conn:
        user = db.get_user_by_id(conn, user_id)
        client = create_authenticated_client(
            app_name="data-syncer",
            user_email=user.email,
            access_token=user.access_token,
        )
        try:
            result = client.post("get_latest_file_to_sync/")
            result.raise_for_status()
            file = FilesToSyncResponse.model_validate_json(result.json()).file
            if file is not None:
                print("Got file to transcribe and upload", file.filename)
                bts = base64.b64decode(file.encoded_bts)
                transcript = transcribe(bts)
                print(
                    f"transcription {file.filename} succesful for {user.email}, uploading to data-syncer"
                )
                upload_transcription_to_queryengine(client, transcript, file)
            else:
                print("No files to transcribe")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 504:
                print(
                    f"Could not reach user {client.app_owner} for /get_latest_file_to_sync"
                )
                return
            else:
                raise e
        except Exception:
            print(
                f"Failed calling {client.app_name} on {client.app_owner}/get_latest_file_to_sync: {traceback.format_exc()}"
            )


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
    else:
        token = settings.whisper_secret_key
        if token is None:
            raise ValueError("WHISPER_SECRET_KEY is not set")

        request = TranscribeRequest.from_bytes(bytes_data, token=token)

        payload = request.model_dump()

        response = requests.post(
            f"http://{settings.whisper_url}/transcribe",
            json=payload,
        )
        transcription = response.json()["transcription"]
        return transcription
