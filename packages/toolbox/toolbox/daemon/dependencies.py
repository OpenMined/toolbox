from fastapi import Request

from toolbox.triggers.scheduler import Scheduler
from toolbox.triggers.trigger_store import TriggerDB


def get_trigger_db(request: Request) -> TriggerDB:
    return request.app.state.trigger_db


def get_scheduler(request: Request) -> Scheduler:
    return request.app.state.scheduler
