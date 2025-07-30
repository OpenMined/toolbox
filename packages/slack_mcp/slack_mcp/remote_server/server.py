import sqlite3
import threading
import traceback
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from slack_mcp.remote_server.background_worker import poll_for_chunks_to_index
from slack_mcp.remote_server.server_db import get_indexer_db, insert_user
from slack_mcp.remote_server.server_models import UserRegistration, UserResponse

router = APIRouter()

stop_event = threading.Event()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/register_user", response_model=UserResponse)
def register_user(
    request: UserRegistration,
    conn_manager: sqlite3.Connection = Depends(get_indexer_db),
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
