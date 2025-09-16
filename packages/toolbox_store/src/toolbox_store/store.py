from pathlib import Path
from typing import Generic, TypeVar, overload

from toolbox_store.db import TBDatabase
from toolbox_store.embedding import get_embedder
from toolbox_store.models import StoreConfig, TBDocument, TBDocumentChunk
from toolbox_store.query_builder import ChunkQueryBuilder, DocumentQueryBuilder

T = TypeVar("T", bound=TBDocument)


class ToolboxStore(Generic[T]):
    # @overload to auto set generic arg to TBDocument (not needed in 3.13+)
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
        self: "ToolboxStore[TBDocument]",
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
    ) -> None:
        self.collection = collection
        self.document_class = document_class or TBDocument
        self.config = config or StoreConfig()
        self.db = TBDatabase(
            collection,
            db_path=db_path,
            config=self.config,
            reset=reset,
            document_class=self.document_class,
        )
        self.db.create_schema()
        self.embedder = get_embedder(self.config)

    def insert_docs(self, docs: list[T], create_embeddings: bool = True) -> None:
        self.db.insert_documents(docs)
        if create_embeddings:
            chunks = self.embed_documents(docs)
            self.insert_chunks(chunks)

    def insert_chunks(self, chunks: list[TBDocumentChunk]) -> None:
        self.db.insert_chunks(chunks)

    def embed_documents(self, docs: list[T]) -> list[TBDocumentChunk]:
        return self.embedder.chunk_and_embed(docs)

    def embed_query(self, query: str | list[str]) -> list[list[float]]:
        return self.embedder.embed_query(query)

    def search_chunks(self) -> ChunkQueryBuilder[T]:
        return ChunkQueryBuilder[T](self, self.document_class)

    def search_documents(self) -> DocumentQueryBuilder[T]:
        return DocumentQueryBuilder[T](self, self.document_class)
