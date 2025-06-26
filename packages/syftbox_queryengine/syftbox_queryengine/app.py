from contextlib import asynccontextmanager
import contextlib

import uvicorn
from fastapi import FastAPI
from fastsyftbox import FastSyftBox
from syftbox_queryengine.fastsyftbox_server import config
from syftbox_queryengine.fastsyftbox_server import router

from syftbox_queryengine.fastsyftbox_server import app
from syftbox_queryengine.settings import settings
from syftbox_queryengine.mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


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
