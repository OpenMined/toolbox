import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec

from toolbox_store.models import StoreConfig, ToolboxDocument


def convert_field(value):
    """Convert Python types to SQLite-compatible types."""
    if isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    return value


class Database:
    def __init__(
        self,
        collection: str,
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

    def create_schema(self) -> None:
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.documents_table} (
                id TEXT PRIMARY KEY,
                metadata JSON,
                source TEXT,
                content TEXT,
                created_at DATETIME
            )
        """)

        # Virtual table for embeddings - minimal fields only
        self.conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.embeddings_table} USING vec0(
                embedding float[{self.config.embedding_dim}],
                document_id TEXT,
                chunk_idx INTEGER
            )
        """)

        # Regular table for chunk metadata
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.chunks_table} (
                document_id TEXT NOT NULL,
                chunk_idx INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_start INTEGER,
                chunk_end INTEGER,
                content_hash TEXT,
                created_at DATETIME,
                PRIMARY KEY (document_id, chunk_idx),
                FOREIGN KEY (document_id) REFERENCES {self.documents_table}(id)
            )
        """)

        self.conn.commit()

    def insert_documents(self, documents: list[ToolboxDocument]):
        for doc in documents:
            # Get all fields that aren't excluded
            doc_dict = doc.model_dump(exclude={"embeddings"})

            # Build query dynamically based on fields
            fields = list(doc_dict.keys())
            placeholders = [f":{field}" for field in fields]

            query = f"""
                INSERT INTO {self.documents_table} ({", ".join(fields)})
                VALUES ({", ".join(placeholders)})
            """

            for key, value in doc_dict.items():
                doc_dict[key] = convert_field(value)

            self.conn.execute(query, doc_dict)

        self.conn.commit()

    def get_all_documents(self) -> list[ToolboxDocument]:
        # utility method
        cursor = self.conn.execute(f"SELECT * FROM {self.documents_table}")
        rows = cursor.fetchall()
        documents = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("metadata"):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            documents.append(ToolboxDocument.model_validate(row_dict))
        return documents


if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent.parent / "data"
    print(data_dir.absolute())
    db_path = data_dir / "test.db"

    db = Database("test", db_path=db_path, reset=True)
    db.create_schema()

    max_docs = 10
    docs_to_insert = []
    for doc in data_dir.glob("*.txt"):
        if len(docs_to_insert) >= max_docs:
            break
        content = doc.read_text()
        document = ToolboxDocument(
            content=content,
            metadata={
                "source": str(doc),
                "created_at": datetime.fromtimestamp(
                    doc.stat().st_ctime, tz=timezone.utc
                ).isoformat(),
                "updated_at": datetime.fromtimestamp(
                    doc.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            },
            source=f"file://{doc.as_posix()}",
        )
        docs_to_insert.append(document)
    db.insert_documents(docs_to_insert)

    all_docs = db.get_all_documents()
    print(f"Retrieved {len(all_docs)} documents from the database.")
    for k, v in all_docs[0].model_dump().items():
        if isinstance(v, str) and len(v) > 100:
            v = v[:100] + "..."
        elif isinstance(v, dict):
            v = json.dumps(v, indent=2)
        print(f"{k}: {v}")
