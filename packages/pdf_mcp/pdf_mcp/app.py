import contextlib
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from pdf_mcp.mcp_server import cleanup_resources, initialize_rag_engine, mcp

port = os.getenv("PDF_MCP_PORT", "8006")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        # Start MCP server first, then initialize RAG engine in background
        await stack.enter_async_context(mcp.session_manager.run())

        # Initialize RAG engine synchronously to ensure proper event loop context

        logger = __import__("logging").getLogger(__name__)
        logger.info("Starting RAG engine initialization...")
        await initialize_rag_engine()
        logger.info("RAG engine initialization completed")

        try:
            yield
        finally:
            # Cleanup resources on shutdown
            await cleanup_resources()


if __name__ == "__main__":
    app = FastAPI(
        lifespan=lifespan,
    )
    app.mount("/mcp", mcp.streamable_http_app())
    uvicorn.run(app, host="0.0.0.0", port=int(port))
