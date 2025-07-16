from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from notes_mcp.background_workers.meeting_indexer import poll_for_new_meetings
from notes_mcp.background_workers.transcriber import poll_for_new_audio_chunks
from notes_mcp.remote_fastapi_server import main_router

meeting_indexer_stop_event = threading.Event()
transcriber_stop_event = threading.Event()


def start_background_workers():
    """Start background workers with optional user authentication."""
    print("Starting meeting indexer")
    meeting_indexer_executor = ThreadPoolExecutor(max_workers=3)
    poll_meetings_producer = threading.Thread(
        target=poll_for_new_meetings,
        args=(meeting_indexer_stop_event, meeting_indexer_executor),
    )
    poll_meetings_producer.start()

    print("Starting transcriber")
    transcriber_executor = ThreadPoolExecutor(max_workers=3)
    poll_transcriber_producer = threading.Thread(
        target=poll_for_new_audio_chunks,
        args=(transcriber_stop_event, transcriber_executor),
    )
    poll_transcriber_producer.start()

    return (
        poll_meetings_producer,
        poll_transcriber_producer,
        meeting_indexer_executor,
        transcriber_executor,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    (
        poll_meetings_producer,
        poll_transcriber_producer,
        meeting_indexer_executor,
        transcriber_executor,
    ) = start_background_workers()

    yield
    print("Cleaning up executor")
    meeting_indexer_executor.shutdown(wait=False)
    transcriber_executor.shutdown(wait=False)

    meeting_indexer_stop_event.set()
    transcriber_stop_event.set()

    poll_meetings_producer.join(timeout=1)
    poll_transcriber_producer.join(timeout=1)


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    app.include_router(main_router)
    uvicorn.run(app, host="0.0.0.0", port=8000)
