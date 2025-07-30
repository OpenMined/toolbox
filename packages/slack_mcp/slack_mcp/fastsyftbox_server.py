from pydantic import BaseModel
import uvicorn
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastsyftbox import FastSyftBox
from fastsyftbox.simple_client import DEV_DEFAULT_OWNER_EMAIL, default_dev_data_dir
from loguru import logger
from syft_core import SyftClientConfig

from slack_mcp import db
from slack_mcp.auth import authenticate
from slack_mcp.db import get_slack_connection
from slack_mcp.models import Chunk
from slack_mcp.settings import settings

APP_NAME = "slack-mcp"


print("settings.dev_mode", settings.dev_mode)
if settings.dev_mode:
    config = SyftClientConfig(
        client_url=8002,  # random
        path="",  # random
        data_dir=default_dev_data_dir(APP_NAME),
        email=DEV_DEFAULT_OWNER_EMAIL,
    )
else:
    config = SyftClientConfig.load()

print("config", config)


router = APIRouter()


# normal fastapi
@router.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse("<html><body><h1>Welcome to Slack MCP</h1>")


# normal fastapi
@router.post("/healthcheck")
def healthcheck():
    return {"status": "ok"}


class GetNewChunksResponse(BaseModel):
    chunks: list[Chunk]


@router.post("/get_new_chunks", tags=["syftbox"])
def get_new_chunks(
    limit: int = 10,
    current_user_email: str = Depends(authenticate),
) -> GetNewChunksResponse:
    try:
        with get_slack_connection() as conn:
            chunks = db.gather_chunks_without_embeddings(conn, limit=limit)
        print(f"returning {len(chunks)} chunks")
        if len(chunks) > 0:
            res = GetNewChunksResponse(chunks=chunks)
            return res.model_dump(mode="json")
        else:
            print("returning empty chunks")
            return GetNewChunksResponse(chunks=[]).model_dump(mode="json")
    except Exception as e:
        import traceback

        logger.error(f"Error querying chunks: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_embeddings", tags=["syftbox"])
def upload_embeddings(
    chunks: list[Chunk],
    current_user_email: str = Depends(authenticate),
):
    try:
        with get_slack_connection() as conn:
            db.upsert_chunks(conn, chunks)
    except Exception as e:
        import traceback

        logger.error(f"Error submitting chunks: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


app = FastSyftBox(
    app_name=APP_NAME,
    syftbox_config=config,
    syftbox_endpoint_tags=[
        "syftbox"
    ],  # endpoints with this tag are also available via Syft RPC
    include_syft_openapi=True,  # Create OpenAPI endpoints for syft-rpc routes
)
app.include_router(router)
app.enable_debug_tool(
    endpoint="/get_latest_file_to_sync",
    example_request=str({}),
    publish=True,
)


if __name__ == "__main__":
    with get_slack_connection() as conn:
        db.create_tables(conn)
    print(settings)
    uvicorn.run(app, host="0.0.0.0", port=8004)
