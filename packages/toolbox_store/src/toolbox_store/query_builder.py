from typing import TYPE_CHECKING, Generic, Self, TypeVar

from toolbox_store.models import RetrievedChunk, TBDocument

if TYPE_CHECKING:
    from toolbox_store.store import ToolboxStore

T = TypeVar("T", bound=TBDocument)


class ChunkQueryBuilder(Generic[T]):
    def __init__(self, store: "ToolboxStore[T]", document_class: type[T]):
        self.store = store
        self.document_class = document_class
        self._semantic_query: str | list[float] | None = None
        self._chunk_limit: int | None = None
        self._chunk_offset: int | None = None

    def semantic(self, query: str | list[float]) -> Self:
        self._semantic_query = query
        return self

    def chunk_limit(self, n: int) -> Self:
        self._chunk_limit = n
        return self

    def chunk_offset(self, n: int) -> Self:
        self._chunk_offset = n
        return self

    def get_chunks(self) -> list[RetrievedChunk]:
        if self._semantic_query is None:
            raise ValueError("No semantic query set. Use .semantic() to set a query.")

        if isinstance(self._semantic_query, str):
            query_embedding = self.store.embed_query(self._semantic_query)[0]
        else:
            query_embedding = self._semantic_query

        query_args = {
            "query_embedding": query_embedding,
        }
        if self._chunk_limit is not None:
            query_args["limit"] = self._chunk_limit
        if self._chunk_offset is not None:
            query_args["offset"] = self._chunk_offset
        retrieved_chunks = self.store.db.semantic_search(**query_args)
        return retrieved_chunks

    def get_documents(self) -> list[T]:
        chunks = self.get_chunks()
        chunks_by_doc_id = {}
        min_distance_by_doc_id = {}

        # Group chunks by document and track minimum distance
        for chunk in chunks:
            if chunk.document_id not in chunks_by_doc_id:
                chunks_by_doc_id[chunk.document_id] = []
                min_distance_by_doc_id[chunk.document_id] = chunk.distance
            chunks_by_doc_id[chunk.document_id].append(chunk)
            min_distance_by_doc_id[chunk.document_id] = min(
                min_distance_by_doc_id[chunk.document_id], chunk.distance
            )

        # Get documents from database
        doc_ids = list(chunks_by_doc_id.keys())
        documents = self.store.db.get_documents(doc_ids)

        # Attach chunks to documents
        for doc in documents:
            doc.chunks = chunks_by_doc_id.get(doc.id, [])

        # Sort documents by minimum chunk distance
        documents.sort(key=lambda doc: min_distance_by_doc_id.get(doc.id, float("inf")))

        return documents
