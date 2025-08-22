import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from loguru import logger
from pydantic import BaseModel

from toolbox.daemon.dependencies import get_trigger_db
from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage daemon lifecycle - startup and shutdown"""
    logger.info("Starting toolbox daemon...")

    try:
        # Initialize trigger store
        logger.debug("Initializing trigger store...")
        app.state.trigger_db = get_db()
        logger.debug("Starting scheduler...")
        app.state.scheduler = Scheduler(app.state.trigger_db)

        # Start scheduler in background thread
        app.state.scheduler_thread = threading.Thread(
            target=app.state.scheduler.run,
            daemon=True,
            name="scheduler-thread",
        )
        app.state.scheduler_thread.start()

        logger.info("Toolbox daemon started successfully")

        yield

    finally:
        logger.info("Shutting down toolbox daemon...")
        if hasattr(app.state, "scheduler") and app.state.scheduler:
            logger.info("Stopping scheduler...")
            app.state.scheduler.running = False

        if (
            hasattr(app.state, "scheduler_thread")
            and app.state.scheduler_thread
            and app.state.scheduler_thread.is_alive()
        ):
            app.state.scheduler_thread.join(timeout=5.0)
            if app.state.scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not stop within timeout")

        if hasattr(app.state, "trigger_db") and app.state.trigger_db:
            logger.info("Closing trigger store...")
            app.state.trigger_db.close()

        logger.info("Toolbox daemon shutdown complete")


class EventModel(BaseModel):
    name: str
    data: dict[str, Any]
    timestamp: datetime
    source: str | None = None


class IngestEventsRequest(BaseModel):
    events: list[EventModel]


class IngestEventsResponse(BaseModel):
    received: int


app_router = APIRouter(prefix="/v1")


@app_router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app_router.post("/events/ingest")
async def ingest_events(
    request: IngestEventsRequest, trigger_db: TriggerDB = Depends(get_trigger_db)
) -> IngestEventsResponse:
    """Ingest events from MCP servers"""
    event_dicts = [event.model_dump() for event in request.events]
    trigger_db.events.create_many(event_dicts)
    return IngestEventsResponse(received=len(request.events))


# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)
app.include_router(app_router)
