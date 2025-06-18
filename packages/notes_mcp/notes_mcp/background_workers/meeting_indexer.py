import sqlite3
import threading
import time
import traceback

from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db
from notes_mcp.fastapi_server import executor
from notes_mcp.models.audio import AudioChunk
from notes_mcp.models.meeting import Meeting

POLL_INTERVAL = 10


def log_error(future):
    exception = future.exception()
    if exception:
        print(f"Background task failed:\n{exception}\n{traceback.format_exc()}")


def poll_for_new_meetings(stop_event: threading.Event):
    conn = sqlite3.connect(db.MEETINGS_DB_PATH)
    conn.row_factory = sqlite3.Row
    db.create_tables(conn)
    while not stop_event.is_set():
        print("Polling for new meetings")
        future = executor.submit(index_meetings)
        future.add_done_callback(log_error)
        time.sleep(POLL_INTERVAL)


def index_meetings():
    client = SimpleRPCClient(app_name="data-syncer", dev_mode=True)
    extract_and_upload_meetings(client)


def extract_and_upload_meetings(client: SimpleRPCClient):
    try:
        result = client.post("/query_transcription_chunks")
        result.raise_for_status()
    except Exception as e:
        print(
            f"Could not reach user {client.app_owner} on {client.app_name}/query_transcription_chunks: {e}"
        )
        return

    transcription_chunks = [
        AudioChunk.from_sql_row(chunk) for chunk in result.transcription_chunks
    ]
    indexed = result.indexed

    print("Found", len(transcription_chunks), "chunks")
    meetings = []
    current_meeting_chunks = []
    if len(transcription_chunks) > 0:
        print("Found", len(transcription_chunks), "chunks")

        previous_start_date = transcription_chunks[0].datetime

        for indexed, chunk in zip(indexed, transcription_chunks):
            if indexed:
                continue

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
        meeting = Meeting(
            filename=f"meeting-{current_meeting_chunks[0].datetime}.txt",
            chunks_ids=[chunk.id for chunk in current_meeting_chunks],
        )
        meetings.append(meeting)
    else:
        print("No new chunks found")

    if len(meetings) > 0:
        payload = [meeting.model_dump() for meeting in meetings]
        client.post("/submit_meetings", json=payload)
