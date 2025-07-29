import contextlib
from contextlib import asynccontextmanager
from threading import Thread

import uvicorn
from fastapi import FastAPI
from fastsyftbox import FastSyftBox

from slack_mcp.background_worker import run_slack_mesage_dump_background_worker_loop
from slack_mcp.fastsyftbox_server import config, router
from slack_mcp.mcp_server import mcp
from slack_mcp.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        thread = Thread(target=run_slack_mesage_dump_background_worker_loop)
        thread.start()
        await stack.enter_async_context(mcp.session_manager.run())
        yield


# app.router.lifespan_context = lifespan

if __name__ == "__main__":
    app = FastSyftBox(
        lifespan=lifespan,
        app_name="slack-mcp",
        syftbox_config=config,
        syftbox_endpoint_tags=[
            "syftbox"
        ],  # endpoints with this tag are also available via Syft RPC
        include_syft_openapi=True,
    )
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=settings.slack_mcp_port)
