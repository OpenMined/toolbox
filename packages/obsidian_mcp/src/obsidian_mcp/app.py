import contextlib
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from obsidian_mcp.mcp_server import mcp
from obsidian_mcp.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # if settings.start_polling_thread:
        #     thread = Thread(target=run_slack_mesage_dump_background_worker_loop)
        #     thread.start()
        await stack.enter_async_context(mcp.session_manager.run())
        yield


# app.router.lifespan_context = lifespan

if __name__ == "__main__":
    print(settings)
    app = FastAPI(
        lifespan=lifespan,
        title="obsidian-mcp",
    )

    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=settings.obsidian_mcp_port)
