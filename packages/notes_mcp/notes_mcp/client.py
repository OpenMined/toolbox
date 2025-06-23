import sqlite3
from typing import Optional, Dict

from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp import db


def create_authenticated_client(
    app_name: str = "data-syncer",
    dev_mode: bool = True,
    user_email: Optional[str] = None,
    access_token: Optional[str] = None,
) -> SimpleRPCClient:
    """Create a SimpleRPCClient with authentication headers."""
    headers = {"X-User-Email": user_email, "X-Access-Token": access_token}
    client = SimpleRPCClient(app_name=app_name, dev_mode=dev_mode, headers=headers)
    return client
