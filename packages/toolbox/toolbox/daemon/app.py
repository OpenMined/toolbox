import threading
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI
from loguru import logger
from pydantic import BaseModel

from toolbox.daemon.daemon_logging import setup_logging
from toolbox.daemon.daemon_settings import DaemonSettings
from toolbox.daemon.dependencies import get_trigger_db
from toolbox.triggers.models import EventBatch
from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI lifecycle - startup and shutdown"""
    # Get settings from app.state or create default
    if hasattr(app.state, "settings"):
        settings = app.state.settings
    else:
        settings = DaemonSettings()
        app.state.settings = settings

    if settings.log_file:
        setup_logging(settings.log_file)

    try:
        logger.info("Starting FastAPI application...")

        logger.debug("Initializing trigger store...")
        app.state.trigger_db = TriggerDB.from_url(settings.db_url)
        logger.debug("Creating scheduler...")
        app.state.scheduler = Scheduler(app.state.trigger_db)

        if settings.enable_scheduler:
            logger.debug("Starting scheduler thread...")
            # Start scheduler in background thread
            app.state.scheduler_thread = threading.Thread(
                target=app.state.scheduler.run,
                daemon=True,
                name="scheduler-thread",
            )
            app.state.scheduler_thread.start()
        else:
            logger.info("Scheduler thread disabled - manual scheduling only")
            app.state.scheduler_thread = None

        logger.info("FastAPI application started successfully")

        yield

    finally:
        logger.info("Shutting down FastAPI application...")

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

        logger.info("FastAPI application shutdown complete")


class IngestEventsResponse(BaseModel):
    received: int


app_router = APIRouter(prefix="/v1")


@app_router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app_router.post("/events/ingest")
async def ingest_events(
    request: EventBatch, trigger_db: TriggerDB = Depends(get_trigger_db)
) -> IngestEventsResponse:
    """Ingest events from MCP servers"""
    event_dicts = [event.model_dump() for event in request.events]
    trigger_db.events.create_many(event_dicts)
    return IngestEventsResponse(received=len(request.events))


def create_app(settings: DaemonSettings | None = None) -> FastAPI:
    """Create FastAPI app with optional settings"""
    app = FastAPI(lifespan=lifespan)
    if settings:
        app.state.settings = settings
    app.include_router(app_router)
    return app
