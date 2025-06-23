import sqlite3
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from notes_mcp import PROJECT_ROOT
from notes_mcp.db import (
    get_meetings_db,
    insert_user,
)
from notes_mcp.models import UserRegistration, UserResponse

BASE_DATA_DIR = PROJECT_ROOT / "data"
N_WORKERS = 2


app = FastAPI()


executor = ThreadPoolExecutor(max_workers=N_WORKERS)


class AudioRequest(BaseModel):
    encoded_bts: str
    audio_chunk_id: int
    timestamp: str
    user_email: str
    device: str = "MacBook Pro Microphone"


class StartWorkersRequest(BaseModel):
    user_email: str


@app.post("/register_user", response_model=UserResponse)
def register_user(
    request: UserRegistration, conn: sqlite3.Connection = Depends(get_meetings_db)
):
    """Register a new user or update existing user's access token."""
    try:
        user_id = insert_user(conn, request.email, request.access_token)
        return UserResponse(
            id=user_id, email=request.email, message="User registered successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register user: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
