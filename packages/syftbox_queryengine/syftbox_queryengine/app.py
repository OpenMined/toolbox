from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from syftbox_queryengine.fastsyftbox_server import app
from syftbox_queryengine.settings import settings


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield
# BE CAREFUL WITH SETTING THE LIFESPAN, BECAUSE IT WONT USE THE HTTP BRIDGE LIFESPAN


# app.router.lifespan_context = lifespan


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.syftbox_queryengine_port)
