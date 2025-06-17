import contextlib
import threading
from notes_mcp import db
from notes_mcp.background_workers.meeting_indexer import poll_for_new_meetings
import uvicorn
from fastapi import FastAPI
from notes_mcp.fastapi_server import app


from notes_mcp.mcp_server import mcp
from contextlib import asynccontextmanager
from notes_mcp.fastapi_server import executor
from notes_mcp.background_workers.meeting_indexer import stop_event as meeting_indexer_stop_event




    


app.mount("/mcp", mcp.streamable_http_app())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)