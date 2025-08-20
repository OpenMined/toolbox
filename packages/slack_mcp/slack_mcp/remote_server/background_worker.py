import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import httpx
import requests
from fastsyftbox.simple_client import SimpleRPCClient
from slack_mcp.models import Chunk
from slack_mcp.remote_server import server_db as db
from slack_mcp.remote_server.server_models import EmbeddingRequest
from slack_mcp.remote_server.server_settings import settings
from slack_mcp.remote_server.user_polling_manager import UserPollingManager
from slack_mcp.syftbox_client import create_authenticated_client

ACTIVITY_THRESHOLD_SECONDS = 10
EMBEDDING_POLL_INTERVAL = 1


def poll_for_chunks_to_index(stop_event: threading.Event, executor: ThreadPoolExecutor):
    with db.get_indexer_db() as conn:
        polling_manager = UserPollingManager(executor)
        while not stop_event.is_set():
            users = db.get_users(conn)
            users_already_processed = set()
            users_inactive = set()
            for user in users:
                if (
                    db.active_since(conn, user.email, ACTIVITY_THRESHOLD_SECONDS)
                    or True
                ):
                    future = polling_manager.submit_job(
                        user.id, _poll_for_new_chunks, (user.id,)
                    )
                    if future is not None:
                        print(f"Polling for new slack messages for user {user.email}")
                    else:
                        users_already_processed.add(user.email)
                else:
                    users_inactive.add(user.email)
            if len(users) == 0:
                print("No users found to emebed")
            time.sleep(EMBEDDING_POLL_INTERVAL)

        # Shutdown the polling manager when the main polling loop stops
        polling_manager.shutdown()
        print("DONE")


def embed(chunks: list[Chunk]) -> list[float]:
    if settings.use_mock_embeddings:
        return [[0.0] * 768 for _ in chunks]
    else:
        response = requests.post(
            f"{settings.nomic_url}:{settings.nomic_port}/embeddings",
            json=[
                EmbeddingRequest(
                    chunk_id=chunk.chunk_id, prompt=chunk.chunk_text
                ).model_dump(mode="json")
                for chunk in chunks
            ],
            headers={"Authorization": f"Bearer {settings.nomic_secret_key}"},
        )
        response.raise_for_status()
        return [embedding["embedding"] for embedding in response.json()]


def upload_embeddings(client: SimpleRPCClient, embeddings: list[Chunk]):
    client.post(
        "upload_embeddings/",
        json=[x.model_dump(mode="json") for x in embeddings],
    )


def _poll_for_new_chunks(user_id: str):
    with db.get_indexer_db() as conn:
        user = db.get_user_by_id(conn, user_id)
        client = create_authenticated_client(
            app_name="slack-mcp",
            user_email=user.email,
            access_token=user.access_token,
        )
        try:
            result = client.post("get_new_chunks/")
            result.raise_for_status()
            chunks = [Chunk.model_validate(chunk) for chunk in result.json()["chunks"]]
            print(f"Found {len(chunks)} new chunks to index")

        except httpx.ReadTimeout:
            print(
                f"Read timeout calling {client.app_name} on {client.app_owner}/get_new_chunks, probably not online",
                flush=True,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 504:
                print(f"Could not reach user {client.app_owner} for /get_new_chunks")
                return
            else:
                raise e
        except Exception:
            print(
                f"Failed calling {client.app_name} on {client.app_owner}/get_new_chunks: {traceback.format_exc()}"
            )
        try:
            embeddings = embed(chunks)
            print(f"embedded {len(chunks)} chunks")
        except Exception:
            print(f"Failed to embed {len(chunks)} chunks: {traceback.format_exc()}")
            return

        try:
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            upload_embeddings(client, chunks)
            print(f"Successfully uploaded {len(chunks)} chunks")
        except httpx.ReadTimeout:
            print(
                f"Read timeout calling {client.app_name} on {client.app_owner}/upload_embeddings, probably not online",
                flush=True,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 504:
                print(
                    f"Could not reach user {client.app_owner} for /upload_embeddings",
                    flush=True,
                )
                return
            else:
                raise e
        except Exception:
            print(
                f"Failed calling {client.app_name} on {client.app_owner}/upload_embeddings: {traceback.format_exc()}",
                flush=True,
            )
