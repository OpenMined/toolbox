import contextlib
import threading
from contextlib import asynccontextmanager
from typing import Optional

from notes_mcp.background_workers.transcriber import poll_for_new_audio_chunks
import uvicorn
from fastapi import FastAPI

from notes_mcp import db
from notes_mcp.background_workers.meeting_indexer import poll_for_new_meetings
from notes_mcp.fastapi_server import app, executor
from notes_mcp.mcp_server import mcp

app.mount("/mcp", mcp.streamable_http_app())


meeting_indexer_stop_event = threading.Event()
transcriber_stop_event = threading.Event()


def start_background_workers():
    """Start background workers with optional user authentication."""
    print("Starting meeting indexer")
    poll_meetings_producer = threading.Thread(
        target=poll_for_new_meetings, args=(meeting_indexer_stop_event,)
    )
    poll_meetings_producer.start()

    print("Starting transcriber")
    poll_transcriber_producer = threading.Thread(
        target=poll_for_new_audio_chunks, args=(transcriber_stop_event,)
    )
    poll_transcriber_producer.start()

    return poll_meetings_producer, poll_transcriber_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())

        poll_meetings_producer, poll_transcriber_producer = start_background_workers()

        yield
        print("Cleaning up executor")
        executor.shutdown(wait=False)

        meeting_indexer_stop_event.set()
        transcriber_stop_event.set()

        poll_meetings_producer.join(timeout=1)
        poll_transcriber_producer.join(timeout=1)


app.router.lifespan_context = lifespan


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
