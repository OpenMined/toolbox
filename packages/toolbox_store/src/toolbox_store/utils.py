import hashlib
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(tz=timezone.utc)


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
