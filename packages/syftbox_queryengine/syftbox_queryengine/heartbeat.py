from threading import Event
from time import sleep

from httpx import Client

from syftbox_queryengine.db import (
    get_all_heartbeat_entries,
    get_query_engine_connection,
)

stop_event = Event()


class QueryEngineAppClient(Client):
    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)

    def heartbeat(self, email: str):
        return self.post("/heartbeat", json={"email": email})


def send_heartbeat(app_name: str, email: str, url: str):
    client = QueryEngineAppClient(base_url=url)
    try:
        response = client.heartbeat(email)
        response.raise_for_status()
    except Exception as e:
        print(
            f" Queryengine could not reach {app_name} for {email} for heartbeat: on {url}/heartbeat {e}"
        )


def heartbeat_loop():
    while not stop_event.is_set():
        with get_query_engine_connection() as conn:
            for heartbeat_entry in get_all_heartbeat_entries(conn):
                if stop_event.is_set():
                    break
                send_heartbeat(
                    heartbeat_entry.app_name,
                    heartbeat_entry.email,
                    heartbeat_entry.url,
                )
        if stop_event.is_set():
            break
        sleep(10)
