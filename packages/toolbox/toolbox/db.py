# conn = sqlite3.connect("mcp.db")
import json
import sqlite3
from pathlib import Path

from toolbox.installed_mcp import InstalledMCP

HOME = Path.home()
TOOLBOX_DB_DIR = HOME / ".toolbox"
TOOLBOX_DB_DIR.mkdir(parents=True, exist_ok=True)
TOOLBOX_DB_PATH = TOOLBOX_DB_DIR / "mcp.db"

conn = sqlite3.connect(TOOLBOX_DB_PATH)
conn.row_factory = sqlite3.Row


def create_table(conn: sqlite3.Connection):
    curr = conn.cursor()
    curr.execute("""CREATE TABLE IF NOT EXISTS mcps (name TEXT, client TEXT, read_access TEXT, write_access TEXT, model TEXT, host TEXT,
                 managed_by TEXT, proxy TEXT, verified TEXT, json_body TEXT, deployment_method TEXT,
                 PRIMARY KEY (name, client))""")


def db_upsert_mcp(conn: sqlite3.Connection, mcp: InstalledMCP):
    curr = conn.cursor()
    curr.execute(
        """
        INSERT INTO mcps (name, client, read_access, write_access, model, host, managed_by, proxy, verified, json_body, deployment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (name, client) DO UPDATE SET
            read_access = excluded.read_access,
            write_access = excluded.write_access,
            model = excluded.model,
            host = excluded.host,
            managed_by = excluded.managed_by,
            proxy = excluded.proxy,
            verified = excluded.verified,
            json_body = excluded.json_body,
            deployment_method = excluded.deployment_method
    """,
        (
            mcp.name,
            json.dumps(mcp.client),
            json.dumps(mcp.read_access),
            json.dumps(mcp.write_access),
            mcp.model,
            mcp.host,
            mcp.managed_by,
            mcp.proxy,
            mcp.verified,
            json.dumps(mcp.json_body),
            mcp.deployment_method,
        ),
    )
    conn.commit()


def db_query_mcps(conn: sqlite3.Connection):
    curr = conn.cursor()
    curr.execute("SELECT * FROM mcps")
    return curr.fetchall()


def db_get_mcps(conn: sqlite3.Connection):
    res = db_query_mcps(conn)
    return [InstalledMCP.from_db_row(row) for row in res]


def db_get_mcps_by_name(conn: sqlite3.Connection, name: str):
    curr = conn.cursor()
    curr.execute("SELECT * FROM mcps WHERE name = ?", (name,))
    rows = curr.fetchall()
    return [InstalledMCP.from_db_row(row) for row in rows]


create_table(conn)
# conn.close()
