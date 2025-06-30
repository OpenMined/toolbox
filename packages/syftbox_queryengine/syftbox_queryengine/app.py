import contextlib
from contextlib import asynccontextmanager
from threading import Thread

import uvicorn
from fastapi import FastAPI
from fastsyftbox import FastSyftBox

from syftbox_queryengine.fastsyftbox_server import app, config, router
from syftbox_queryengine.heartbeat import (
    heartbeat_loop,
    stop_event as heartbeat_stop_event,
)
from syftbox_queryengine.mcp_server import mcp
from syftbox_queryengine.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        thread = Thread(target=heartbeat_loop)
        thread.start()
        await stack.enter_async_context(mcp.session_manager.run())
        yield
        heartbeat_stop_event.set()
        thread.join()


# app.router.lifespan_context = lifespan


if __name__ == "__main__":
    app = FastSyftBox(
        lifespan=lifespan,
        app_name="data-syncer",
        syftbox_config=config,
        syftbox_endpoint_tags=[
            "syftbox"
        ],  # endpoints with this tag are also available via Syft RPC
        include_syft_openapi=True,  # Create OpenAPI endpoints for syft-rpc routes
    )
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    app.enable_debug_tool(
        endpoint="/get_latest_file_to_sync",
        example_request=str({}),
        publish=True,
    )
    uvicorn.run(app, host="0.0.0.0", port=settings.syftbox_queryengine_port)
