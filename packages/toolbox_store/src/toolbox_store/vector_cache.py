import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np


def serialize_float32(vector: np.ndarray | list[float]) -> bytes:
    if isinstance(vector, list):
        vector = np.array(vector, dtype=np.float32)
    elif vector.dtype != np.float32:
        vector = vector.astype(np.float32)
    return vector.tobytes()


def deserialize_float32(blob: bytes) -> np.ndarray:
    """Deserialize bytes back to numpy array."""
    return np.frombuffer(blob, dtype=np.float32)


class VectorCache:
    """Fast hash-based vector cache using SQLite with BLOB storage."""

    def __init__(self, db_path: str | Path = ":memory:", reset: bool = False):
        """
        Initialize vector cache.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory
            reset: If True, drops existing cache table and recreates
        """
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path

        if reset and db_path != ":memory:" and isinstance(self.db_path, Path):
            if self.db_path.exists():
                self.db_path.unlink()

        self.conn = sqlite3.connect(str(db_path))
        self._init_table(reset)
        self._init_db()

    def _init_table(self, reset: bool = False):
        """Create cache table."""
        if reset:
            self.conn.execute("DROP TABLE IF EXISTS vector_cache")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vector_cache (
                hash TEXT PRIMARY KEY,
                vector BLOB NOT NULL
            )
        """)
        self.conn.commit()

    def _init_db(self):
        """Apply SQLite optimizations for fast reads/writes."""
        self.conn.execute("PRAGMA journal_mode = WAL")  # Concurrent reads
        self.conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
        self.conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        self.conn.execute("PRAGMA temp_store = MEMORY")
        self.conn.commit()

    def put(self, hash_key: str, vector: np.ndarray | list[float]) -> None:
        """
        Insert or update a vector in cache.

        Args:
            hash_key: Unique identifier for the vector
            vector: Vector as numpy array or list of floats
        """
        self.conn.execute(
            "INSERT OR REPLACE INTO vector_cache (hash, vector) VALUES (?, ?)",
            (hash_key, serialize_float32(vector)),
        )
        self.conn.commit()

    def get(self, hash_key: str) -> Optional[np.ndarray]:
        """
        Retrieve a vector from cache.

        Args:
            hash_key: Unique identifier for the vector

        Returns:
            Vector as numpy array, or None if not found
        """
        cursor = self.conn.execute(
            "SELECT vector FROM vector_cache WHERE hash = ?", (hash_key,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return deserialize_float32(row[0])

    def put_batch(self, vectors: dict[str, np.ndarray | list[float]]) -> None:
        """
        Batch insert/update vectors for better performance.

        Args:
            vectors: Dict mapping hash keys to vectors
        """
        data = [
            (hash_key, serialize_float32(vector))
            for hash_key, vector in vectors.items()
        ]
        self.conn.executemany(
            "INSERT OR REPLACE INTO vector_cache (hash, vector) VALUES (?, ?)", data
        )
        self.conn.commit()

    def get_batch(self, hash_keys: list[str]) -> dict[str, np.ndarray]:
        """
        Batch retrieve vectors.

        Args:
            hash_keys: List of hash keys to retrieve

        Returns:
            Dict mapping hash keys to vectors (only includes found vectors)
        """
        placeholders = ",".join("?" * len(hash_keys))
        cursor = self.conn.execute(
            f"SELECT hash, vector FROM vector_cache WHERE hash IN ({placeholders})",
            hash_keys,
        )

        result = {}
        for row in cursor:
            result[row[0]] = deserialize_float32(row[1])

        return result

    def exists(self, hash_key: str) -> bool:
        """Check if a hash key exists in cache."""
        cursor = self.conn.execute(
            "SELECT 1 FROM vector_cache WHERE hash = ? LIMIT 1", (hash_key,)
        )
        return cursor.fetchone() is not None

    def delete(self, hash_key: str) -> bool:
        """
        Delete a vector from cache.

        Returns:
            True if vector was deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM vector_cache WHERE hash = ?", (hash_key,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> None:
        """Clear all vectors from cache."""
        self.conn.execute("DELETE FROM vector_cache")
        self.conn.commit()

    def size(self) -> int:
        """Get number of vectors in cache."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM vector_cache")
        return cursor.fetchone()[0]

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __len__(self) -> int:
        return self.size()

    def __contains__(self, hash_key: str) -> bool:
        return self.exists(hash_key)
