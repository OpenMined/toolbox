import sqlite3
from pathlib import Path
from typing import Any, Generic, TypeVar, overload

import numpy as np
import sqlite_vec

from toolbox_store.filters import build_where_clause
from toolbox_store.models import (
    StoreConfig,
    TBDocument,
    is_valid_field_identifier,
)
from toolbox_store.retrieved_chunks import RetrievedChunk, TBDocumentChunk

T = TypeVar("T", bound=TBDocument)


def deserialize_float32(blob: bytes) -> list[float]:
    """Deserialize bytes back to list of floats."""
    return np.frombuffer(blob, dtype=np.float32).tolist()


class TBDatabase(Generic[T]):
    @overload
    def __init__(
        self,
        collection: str,
        document_class: type[T],
        db_path: str | Path = ":memory:",
        config: StoreConfig | None = None,
        reset: bool = False,
    ) -> None: ...

    @overload
    def __init__(
        self: "TBDatabase[TBDocument]",
        collection: str,
        document_class: None = None,
        db_path: str | Path = ":memory:",
        config: StoreConfig | None = None,
        reset: bool = False,
    ) -> None: ...

    def __init__(
        self,
        collection: str,
        document_class: type[T] | None = None,
        db_path: str | Path = ":memory:",
        config: StoreConfig | None = None,
        reset: bool = False,
    ):
        self.db_path = Path(db_path)
        if reset and db_path != ":memory:":
            self.reset()
        self.collection = collection
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.config = config or StoreConfig()
        self.document_class = document_class or TBDocument

    def reset(self):
        self.db_path.unlink(missing_ok=True)

    @property
    def documents_table(self) -> str:
        return f"{self.collection}_documents"

    @property
    def embeddings_table(self) -> str:
        return f"{self.collection}_embeddings_vec"

    @property
    def chunks_table(self) -> str:
        return f"{self.collection}_chunks"

    @property
    def fts_table(self) -> str:
        return f"{self.collection}_fts"

    def create_schema(self) -> None:
        try:
            # Build column list
            columns = [
                "id TEXT PRIMARY KEY",
                "metadata JSON",
                "source TEXT",
                "content TEXT",
                "created_at DATETIME",
                "updated_at DATETIME",
                "content_hash TEXT",
            ]

            # Add extra columns from document class
            for name, type_ in self.document_class.schema_extra_columns():
                columns.append(f"{name} {type_}")

            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.documents_table} (
                    {", ".join(columns)}
                )
            """)

            # Virtual table for embeddings - minimal fields only
            self.conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self.embeddings_table} USING vec0(
                    embedding float[{self.config.embedding_dim}] distance_metric={self.config.distance_metric},
                    document_id TEXT,
                    chunk_idx INTEGER
                )
            """)

            # Regular table for chunk metadata
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.chunks_table} (
                    document_id TEXT NOT NULL,
                    chunk_idx INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    chunk_start INTEGER,
                    chunk_end INTEGER,
                    content_hash TEXT,
                    created_at DATETIME,
                    PRIMARY KEY (document_id, chunk_idx),
                    FOREIGN KEY (document_id) REFERENCES {self.documents_table}(id)
                )
            """)
            self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.chunks_table}_document_id
                ON {self.chunks_table}(document_id)
            """)

            # FTS5 virtual table for full-text search
            self.conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self.fts_table} USING fts5(
                    document_id UNINDEXED,
                    chunk_idx UNINDEXED,
                    content,
                    tokenize='porter unicode61'
                )
            """)

            # Execute any schema modifications defined by the document class
            extra_statements = self.document_class.schema_extra(
                self.documents_table,
                self.chunks_table,
                self.embeddings_table,
                self.fts_table,
            )
            for statement in extra_statements:
                self.conn.execute(statement)

            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def insert_documents(self, documents: list[T]):
        if not documents:
            return

        try:
            # Get fields from first document to build query
            first_doc = documents[0].to_sql_dict()
            fields = list(first_doc.keys())
            placeholders = [f":{field}" for field in fields]

            query = f"""
                INSERT OR REPLACE INTO {self.documents_table} ({", ".join(fields)})
                VALUES ({", ".join(placeholders)})
            """

            # Prepare data for bulk insert with named parameters
            data = []
            for doc in documents:
                data.append(doc.to_sql_dict())

            self.conn.executemany(query, data)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def insert_chunks(self, chunks: list[TBDocumentChunk]) -> None:
        if not chunks:
            return

        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(
                    "Chunk embedding cannot be None when inserting chunks."
                )
            if len(chunk.embedding) != self.config.embedding_dim:
                raise ValueError(
                    f"Chunk embedding dimension {len(chunk.embedding)} does not match dimension {self.config.embedding_dim}."
                )

        try:
            # Prepare chunk data for bulk insert with named parameters
            chunk_data = []
            for chunk in chunks:
                chunk_data.append(chunk.to_sql_dict())

            # Get fields from first chunk to build query
            if chunk_data:
                fields = list(chunk_data[0].keys())
                placeholders = [f":{field}" for field in fields]

                # Bulk insert chunks with named parameters
                self.conn.executemany(
                    f"""
                    INSERT OR REPLACE INTO {self.chunks_table}
                    ({", ".join(fields)})
                    VALUES ({", ".join(placeholders)})
                    """,
                    chunk_data,
                )

            # Prepare embedding data for bulk insert (serialize embeddings)
            embedding_data = [
                (
                    sqlite_vec.serialize_float32(emb.embedding),
                    emb.document_id,
                    emb.chunk_idx,
                )
                for emb in chunks
            ]

            # Bulk insert embeddings
            self.conn.executemany(
                f"""
                INSERT INTO {self.embeddings_table}
                (embedding, document_id, chunk_idx)
                VALUES (?, ?, ?)
                """,
                embedding_data,
            )

            # Populate FTS5 table for full-text search
            fts_data = [
                (chunk.document_id, chunk.chunk_idx, chunk.content) for chunk in chunks
            ]
            self.conn.executemany(
                f"""
                INSERT INTO {self.fts_table}
                (document_id, chunk_idx, content)
                VALUES (?, ?, ?)
                """,
                fts_data,
            )

            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def get_documents(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int = 0,
        order_by: str = "id",
        sort_ascending: bool = True,
    ) -> list[T]:
        """
        Get documents with optional filtering and pagination.

        Args:
            filters: Django-style filters (e.g., {'metadata.author': 'john', 'created_at__gte': '2024-01-01'})
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            order_by: Field to order results by (default is 'id')
            sort_ascending: Whether to sort in ascending order (default is True)
        """

        # Build base query
        query = f"SELECT * FROM {self.documents_table} d"
        params = {}

        # Add WHERE clause if filters provided
        if filters:
            where_clause, filter_params = build_where_clause(filters)
            if where_clause:
                query += f" WHERE {where_clause}"
                params.update(filter_params)

        if (
            order_by not in self.document_class.model_fields
            or not is_valid_field_identifier(order_by)
        ):
            raise ValueError(f"Invalid order_by field: {order_by}")
        direction = "ASC" if sort_ascending else "DESC"
        query += f" ORDER BY {order_by} {direction}"

        # Add LIMIT and OFFSET
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        if offset > 0:
            query += f" OFFSET {int(offset)}"

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        return [self.document_class.from_sql_row(row) for row in rows]

    def get_documents_by_id(self, ids: list[str]) -> list[T]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        cursor = self.conn.execute(
            f"SELECT * FROM {self.documents_table} WHERE id IN ({placeholders})", ids
        )
        rows = cursor.fetchall()
        return [self.document_class.from_sql_row(row) for row in rows]

    def semantic_search(
        self,
        query_embedding: list[float],
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[RetrievedChunk]:
        """
        Perform semantic search using a query embedding.
        Returns list of RetrievedEmbedding objects with distance scores.
        """

        params_dict = {
            "query_embedding": sqlite_vec.serialize_float32(query_embedding),
            "limit": limit,
            "offset": offset,
            "total_limit": limit + offset,
        }

        if filters:
            where_clause, where_params = build_where_clause(filters)
            if any(key in params_dict for key in where_params):
                raise ValueError("Filter parameters conflict with reserved names.")
            params_dict.update(where_params)
            where_clause = f"""AND document_id IN (
                    SELECT id FROM {self.documents_table} d
                    WHERE {where_clause}
                )"""
        else:
            where_clause, where_params = "", None

        # Single query joining embeddings with chunks to get all needed data
        # Note: sqlite-vec requires LIMIT in the virtual table query, we apply OFFSET in outer query
        cursor = self.conn.execute(
            f"""
            SELECT
                c.*,
                e.*
            FROM (
                SELECT *, distance FROM {self.embeddings_table}
                WHERE embedding MATCH :query_embedding
                {where_clause}
                ORDER BY distance
                LIMIT :total_limit
            ) as e
            INNER JOIN {self.chunks_table} c
                ON e.document_id = c.document_id
                AND e.chunk_idx = c.chunk_idx
            ORDER BY distance
            LIMIT :limit OFFSET :offset
            """,
            params_dict,
        )

        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            embedding_blob = row_dict.get("embedding", None)
            if isinstance(embedding_blob, bytes):
                row_dict["embedding"] = deserialize_float32(embedding_blob)
            else:
                row_dict["embedding"] = None

            results.append(RetrievedChunk.from_sql_row(row_dict))

        return results

    def keyword_search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[RetrievedChunk]:
        """
        Perform keyword search using FTS5.
        Returns list of RetrievedChunk objects with BM25 rank scores.
        """

        params_dict = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }

        if filters:
            where_clause, where_params = build_where_clause(filters)
            if any(key in params_dict for key in where_params):
                raise ValueError("Filter parameters conflict with reserved names.")
            params_dict.update(where_params)
            where_clause = f"""AND f.document_id IN (
                    SELECT id FROM {self.documents_table} d
                    WHERE {where_clause}
                )"""
        else:
            where_clause = ""

        # Query FTS5 table and join with chunks to get full data
        cursor = self.conn.execute(
            f"""
            SELECT
                c.*,
                f.rank as distance
            FROM {self.fts_table} f
            INNER JOIN {self.chunks_table} c
                ON f.document_id = c.document_id
                AND f.chunk_idx = c.chunk_idx
            WHERE {self.fts_table} MATCH :query
            {where_clause}
            ORDER BY rank
            LIMIT :limit OFFSET :offset
            """,
            params_dict,
        )

        rows = cursor.fetchall()
        return [RetrievedChunk.from_sql_row(row) for row in rows]

    def get_docs_without_embeddings(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[T]:
        """
        Retrieve documents that do not have any associated embeddings.
        """

        # all docs where count chunks is 0
        cursor = self.conn.execute(
            f"""
                SELECT d.* FROM {self.documents_table} d
                LEFT JOIN {self.chunks_table} c ON d.id = c.document_id
                WHERE c.document_id IS NULL
                LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        rows = cursor.fetchall()
        return [self.document_class.from_sql_row(row) for row in rows]

    def stats(self) -> dict[str, Any]:
        """Get basic stats about the database."""
        cursor = self.conn.execute(
            f"SELECT COUNT(*) as count FROM {self.documents_table}"
        )
        doc_count = cursor.fetchone()["count"]

        cursor = self.conn.execute(f"SELECT COUNT(*) as count FROM {self.chunks_table}")
        chunk_count = cursor.fetchone()["count"]

        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "embedding_dim": self.config.embedding_dim,
            "distance_metric": self.config.distance_metric,
        }

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
