import sqlite3
import threading
import time
import traceback

from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db
from notes_mcp.fastapi_server import executor
from notes_mcp.models.audio import AudioChunk, TranscriptionChunksResult
from notes_mcp.models.meeting import Meeting
from notes_mcp.syftbox_client import create_authenticated_client

POLL_INTERVAL = 10


def log_error(future):
    exception = future.exception()
    if exception:
        print(f"Background task failed:\n{exception}\n{traceback.format_exc()}")


def poll_for_new_meetings(stop_event: threading.Event):
    while not stop_event.is_set():
        with db.get_meetings_db() as conn:
            users = db.get_users(conn)
            for user in users:
                print("Polling for new meetings")
                future = executor.submit(index_meetings, user.email, user.access_token)
                future.add_done_callback(log_error)
            if len(users) == 0:
                print("No users found to index meetings")

            time.sleep(POLL_INTERVAL)


def index_meetings(user_email: str, access_token: str):
    client = create_authenticated_client(
        app_name="data-syncer",
        user_email=user_email,
        access_token=access_token,
    )
    extract_and_upload_meetings(client)


def extract_and_upload_meetings(client: SimpleRPCClient):
    try:
        response = client.post("/query_transcription_chunks")
        response.raise_for_status()
        res = TranscriptionChunksResult.model_validate_json(response.json())
    except Exception as e:
        print(
            f"Failed calling syft://{client.app_owner} on {client.app_name}/query_transcription_chunks: {e}"
        )
        return

    transcription_chunks = res.transcription_chunks
    indexed = res.indexed

    meetings = []
    current_meeting_chunks = []
    if len(transcription_chunks) > 0:
        print(
            "Found",
            len(transcription_chunks),
            "new transcription chunks to index for meetings",
        )

        previous_start_date = transcription_chunks[0].datetime

        for indexed, chunk in zip(indexed, transcription_chunks):
            if indexed:
                continue
            print(chunk.datetime, previous_start_date)
            time_diff = (chunk.datetime - previous_start_date).total_seconds() / 60
            if time_diff > 30:
                if current_meeting_chunks:
                    meeting = Meeting(
                        filename=f"meeting_{current_meeting_chunks[0].datetime}.txt",
                        chunks_ids=[chunk.id for chunk in current_meeting_chunks],
                    )
                    meetings.append(meeting)
                current_meeting_chunks = [chunk]
                previous_start_date = chunk.datetime
            else:
                current_meeting_chunks.append(chunk)

        if len(current_meeting_chunks) > 0:
            meeting = Meeting(
                filename=f"meeting-{current_meeting_chunks[0].datetime}.txt",
                chunks_ids=[chunk.id for chunk in current_meeting_chunks],
            )
            meetings.append(meeting)
    else:
        print("No new transcription chunks found to index for meetings")

    if len(meetings) > 0:
        payload = [meeting.model_dump() for meeting in meetings]
        client.post("/submit_meetings", json=payload)
