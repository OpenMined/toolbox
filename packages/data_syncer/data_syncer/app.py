from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from data_syncer.fastsyftbox_server import app

# def syncer_thread(stop_event):
#     with get_connection() as sync_conn:
#         while not stop_event.is_set():
#             # get all files in SCREENPIPE_DATA_DIR
#             print("Finding files to sync")
#             sync_files(sync_conn)
#             sleep(10)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield


# app.router.lifespan_context = lifespan


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8002)
