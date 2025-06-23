import base64
from datetime import datetime
from pathlib import Path
import sqlite3
from time import sleep
from contextlib import contextmanager

from syftbox_queryengine.db import (
    get_all_audio_chunks,
    get_query_engine_connection,
    get_screenpipe_connection,
    get_synced_audio_chunks,
)
from syftbox_queryengine.models import AudioChunk, AudioChunkDB
import requests


URL = "http://localhost:8000"
HOME = Path.home()


def get_files_to_sync(conn) -> list[AudioChunkDB]:
    with get_screenpipe_connection() as conn:
        all_audio_chunks = get_all_audio_chunks(conn)
        files_to_sync = []

    with get_query_engine_connection() as conn:
        synced_audio_chunks = get_synced_audio_chunks(conn)

    synced_files_set = set([chunk.file_path for chunk in synced_audio_chunks])
    for chunk in all_audio_chunks:
        if chunk.file_path not in synced_files_set:
            files_to_sync.append(chunk)
    return files_to_sync
