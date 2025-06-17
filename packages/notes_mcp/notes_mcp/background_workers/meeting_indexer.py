import sqlite3
import threading
import time
import traceback
from notes_mcp import db
from notes_mcp.models.meeting import Meeting
from notes_mcp.fastapi_server import executor

POLL_INTERVAL = 10

stop_event = threading.Event()

def log_error(future):
    exception = future.exception()
    if exception:
        print(f"Background task failed:\n{exception}\n{traceback.format_exc()}")

def poll_for_new_meetings():
    conn = sqlite3.connect(db.MEETINGS_DB_PATH)
    conn.row_factory = sqlite3.Row
    db.create_tables(conn)
    while not stop_event.is_set():
        print("Polling for new meetings")
        chunks, indexed = db.get_audio_chunks(conn)
        if len(chunks) > 0:
            future = executor.submit(index_meetings)
            future.add_done_callback(log_error)
        else:
            print("No new chunks found")
        time.sleep(POLL_INTERVAL)
        
def index_meetings():
    print("Indexing meetings")
    conn = sqlite3.connect(db.MEETINGS_DB_PATH)
    conn.row_factory = sqlite3.Row
    meetings = extract_meetings(conn)
    print("Found", len(meetings), "meetings")
    for meeting in meetings:
        print("Inserting new meeting", meeting.filename)
        db.insert_meeting(conn, meeting.filename, meeting.chunks_ids)

def extract_meetings(conn):
    print("Extracting meetings")
    chunks, indexed = db.get_audio_chunks(conn)
    print("Found", len(chunks), "chunks")
    meetings = []
    current_meeting_chunks = []
    if len(chunks) > 0:
        previous_start_date = chunks[0].datetime

        for indexed, chunk in zip(indexed, chunks):
            if indexed:
                continue
            
            time_diff = (chunk.datetime - previous_start_date).total_seconds() / 60
            if time_diff > 30:
                if current_meeting_chunks:
                    meeting = Meeting(
                        filename=f"meeting_{current_meeting_chunks[0].datetime}.txt",
                        chunks_ids=[chunk.id for chunk in current_meeting_chunks],
                        chunks=current_meeting_chunks,
                    )
                    meetings.append(meeting)
                current_meeting_chunks = [chunk]
                previous_start_date = chunk.datetime
            else:
                current_meeting_chunks.append(chunk)
        meeting = Meeting(
                        filename=f"meeting-{current_meeting_chunks[0].datetime}.txt",
                        chunks_ids=[chunk.id for chunk in current_meeting_chunks],
                        chunks=current_meeting_chunks
                    )
        meetings.append(meeting)
    print("Found", len(meetings), "meetings")
    return meetings
            
            
