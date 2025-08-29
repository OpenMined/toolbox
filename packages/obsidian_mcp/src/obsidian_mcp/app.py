import asyncio
import contextlib
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from obsidian_mcp.file_watcher import watch_vault
from obsidian_mcp.mcp_server import mcp
from obsidian_mcp.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # from toolbox_events.settings import EventSinkSettings
    # import sys
    # print(EventSinkSettings().model_dump_json(indent=2), file=sys.stderr)
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())

        # Start file watcher if vault path is configured
        if settings.obsidian_vault_path:
            task = asyncio.create_task(watch_vault(settings.obsidian_vault_path))
            stack.callback(task.cancel)

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
