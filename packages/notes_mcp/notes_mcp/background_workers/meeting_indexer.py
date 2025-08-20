import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db
from notes_mcp.background_workers.user_polling_manager import UserPollingManager
from notes_mcp.models.audio import AudioChunksResult
from notes_mcp.models.meeting import Meeting
from notes_mcp.syftbox_client import create_authenticated_client

MEETING_POLL_INTERVAL = 1

ACTIVITY_THRESHOLD_SECONDS = 10


def log_error(future):
    exception = future.exception()
    if exception:
        print(f"Background task failed:\n{exception}\n{traceback.format_exc()}")


def poll_for_new_meetings(stop_event: threading.Event, executor: ThreadPoolExecutor):
    polling_manager = UserPollingManager(executor)
    while not stop_event.is_set():
        with db.get_notes_db() as conn:
            users = db.get_users(conn)
            users_already_processed = set()
            users_inactive = set()

            for user in users:
                if db.active_since(conn, user.email, ACTIVITY_THRESHOLD_SECONDS):
                    future = polling_manager.submit_job(
                        user.id, callback=index_meetings, args=(user.id,)
                    )
                    if future is not None:
                        print(f"User {user.email} is active, polling for new meetings")
                        future.add_done_callback(log_error)
                    else:
                        users_already_processed.add(user.email)
                else:
                    users_inactive.add(user.email)

            if len(users) == 0:
                print("No users found to index meetings")

            time.sleep(MEETING_POLL_INTERVAL)


def index_meetings(user_id: int):
    with db.get_notes_db() as conn:
        user = db.get_user_by_id(conn, user_id)
        client = create_authenticated_client(
            app_name="data-syncer",
            user_email=user.email,
            access_token=user.access_token,
        )
        extract_and_upload_meetings(client)


def extract_and_upload_meetings(client: SimpleRPCClient):
    try:
        response = client.post("/query_transcription_chunks")
        response.raise_for_status()
        res = AudioChunksResult.model_validate_json(response.json())
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 504:
            print(
                f"Could not reach user {client.app_owner} for /query_transcription_chunks"
            )
            return
        else:
            raise e
    except Exception as e:
        print(
            f"Failed calling syft://{client.app_owner} on {client.app_name}/query_transcription_chunks: {e}"
        )
        return

    audio_chunks = res.audio_chunks
    indexed = res.indexed
    n_not_indexed = sum([not i for i in indexed])

    meetings = []
    current_meeting_chunks = []
    if len(audio_chunks) > 0:
        print(
            "Found",
            n_not_indexed,
            "new transcription chunks to index for meetings",
        )

        previous_start_date = audio_chunks[0].datetime

        for is_indexed, audio_chunk in zip(indexed, audio_chunks):
            if is_indexed:
                continue
            print(audio_chunk.datetime, previous_start_date)
            time_diff = (
                audio_chunk.datetime - previous_start_date
            ).total_seconds() / 60
            if time_diff > 30:
                if current_meeting_chunks:
                    meeting = Meeting(
                        filename=f"meeting_{current_meeting_chunks[0].datetime}.txt",
                        audio_chunk_ids=[chunk.id for chunk in current_meeting_chunks],
                    )
                    meetings.append(meeting)
                current_meeting_chunks = [audio_chunk]
                previous_start_date = audio_chunk.datetime
            else:
                current_meeting_chunks.append(audio_chunk)

        if len(current_meeting_chunks) > 0:
            meeting = Meeting(
                filename=f"meeting-{current_meeting_chunks[0].datetime}.txt",
                audio_chunk_ids=[
                    audio_chunk.id for audio_chunk in current_meeting_chunks
                ],
            )
            meetings.append(meeting)
    else:
        print("No new transcription chunks found to index for meetings")

    if len(meetings) > 0:
        for meeting in meetings:
            print(
                f"found meeting {meeting.filename} with audio chunk ids {meeting.audio_chunk_ids}"
            )
        payload = [meeting.model_dump() for meeting in meetings]
        client.post("/submit_meetings", json=payload)
    else:
        print(f"No new meetings found from {n_not_indexed} new transcription chunks")
