import sqlite3
from concurrent.futures import ThreadPoolExecutor
import traceback

from notes_mcp.models.heartbeat import HeartbeatRequest
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, APIRouter
from pydantic import BaseModel

from notes_mcp import PROJECT_ROOT
from notes_mcp.db import (
    get_notes_db,
    insert_user,
    set_heartbeat,
)
from notes_mcp.models import UserRegistration, UserResponse

BASE_DATA_DIR = PROJECT_ROOT / "data"
N_WORKERS = 2


main_router = APIRouter()


class AudioRequest(BaseModel):
    encoded_bts: str
    audio_chunk_id: int
    timestamp: str
    user_email: str
    device: str = "MacBook Pro Microphone"


class StartWorkersRequest(BaseModel):
    user_email: str


@main_router.post("/register_user", response_model=UserResponse)
def register_user(
    request: UserRegistration,
    conn_manager: sqlite3.Connection = Depends(get_notes_db),
):
    """Register a new user or update existing user's access token."""
    try:
        with conn_manager as conn:
            user_id = insert_user(conn, request.email, request.access_token)
            return UserResponse(
                id=user_id, email=request.email, message="User registered successfully"
            )
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Failed to register user: {traceback.format_exc()}"
        )


@main_router.post("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@main_router.post("/heartbeat")
def heartbeat(request: HeartbeatRequest):
    with get_notes_db() as conn:
        set_heartbeat(conn, request.email)
    return {"status": "ok"}


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(main_router)
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
