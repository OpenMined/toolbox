

import base64
from datetime import datetime
from pathlib import Path
import sqlite3
from time import sleep

import requests


URL = "http://localhost:8000"
HOME = Path.home()

SQLITE_DB_PATH = HOME / ".data-syncer-mcp" / "data.db"
SCREENPIPE_DATA_DIR = HOME / ".screenpipe" / "data"

SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


file_id_counter = 0

conn = sqlite3.connect(SQLITE_DB_PATH)
conn.row_factory = sqlite3.Row


def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synced_files (
            file_name TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    
    
def get_synced_files(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM synced_files")
    return [row["file_name"] for row in cursor.fetchall()]
    
def mark_file_as_synced(conn, file_name):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO synced_files (file_name) VALUES (?)", (file_name,))
    conn.commit()

def get_files_to_sync(conn):
    files = list(SCREENPIPE_DATA_DIR.glob("*"))
    files = [f for f in files if "input" in f.name]
    files_to_sync = []
    for file in files:
        if file.name not in get_synced_files(conn):
            files_to_sync.append(file)
    return files_to_sync


def sync_files(conn):
    files = get_files_to_sync(conn)
    for file in files:
        print("Syncing file", file)
        bts = open(file, "rb").read()
        global file_id_counter
        file_id = file_id_counter
        timestamp = datetime.fromtimestamp(file.stat().st_mtime)
        file_id_counter += 1
        payload = {
            "user_email": "koen@openmined.org",
            "file_name": file.name,
            "encoded_bts": base64.b64encode(bts).decode('utf-8'),
            "id": file_id,
            "timestamp": str(timestamp),
            "device": "MacBook Pro Microphone"}
        print(payload)
        response = requests.post(f"{URL}/upload_audio_chunk",
                                 json=payload)
        print(response.json())
        mark_file_as_synced(conn, file.name)
        
create_tables(conn)
        
while True:
    # get all files in SCREENPIPE_DATA_DIR
    print("Finding files to sync")
    sync_files(conn)
    sleep(10)