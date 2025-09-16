from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

from toolbox_store.models import RetrievedChunk, TBDocument

if TYPE_CHECKING:
    from toolbox_store.store import ToolboxStore

T = TypeVar("T", bound=TBDocument)


class DocumentQueryBuilder(Generic[T]):
    """Query builder for document-level queries with filtering and pagination."""

    def __init__(self, store: "ToolboxStore[T]", document_class: type[T]):
        self.store = store
        self.document_class = document_class
        self._filters: dict[str, Any] | None = None
        self._limit: int | None = None
        self._offset: int = 0

    def where(self, filters: dict[str, Any]) -> Self:
        """Add filters to the query."""
        if self._filters is None:
            self._filters = {}
        self._filters.update(filters)
        return self

    def limit(self, n: int) -> Self:
        """Set the maximum number of documents to return."""
        self._limit = n
        return self

    def offset(self, n: int) -> Self:
        """Set the number of documents to skip."""
        self._offset = n
        return self

    def get(self) -> list[T]:
        """Execute the query and return documents."""
        return self.store.db.get_documents(
            filters=self._filters, limit=self._limit, offset=self._offset
        )


class ChunkQueryBuilder(Generic[T]):
    def __init__(self, store: "ToolboxStore[T]", document_class: type[T]):
        self.store = store
        self.document_class = document_class
        self._semantic_query: str | list[float] | None = None
        self._keyword_query: str | None = None
        self._chunk_limit: int | None = None
        self._chunk_offset: int | None = None
        self._filters: dict[str, Any] | None = None

        self._hybrid_method: str = "rrf"
        self._hybrid_k: int = 60

    def semantic(self, query: str | list[float]) -> Self:
        self._semantic_query = query
        return self

    def keyword(self, query: str) -> Self:
        self._keyword_query = query
        return self

    def where(self, filters: dict[str, Any]) -> Self:
        if self._filters is None:
            self._filters = {}
        self._filters.update(filters)
        return self

    def chunk_limit(self, n: int) -> Self:
        self._chunk_limit = n
        return self

    def chunk_offset(self, n: int) -> Self:
        self._chunk_offset = n
        return self

    def hybrid(self, method: str = "rrf", **kwargs) -> Self:
        """Configure hybrid search method.

        Args:
            method: Currently only 'rrf' (Reciprocal Rank Fusion) is supported
            **kwargs: Method-specific parameters (e.g., k=60 for RRF)

        Returns:
            Self for chaining
        """
        self._hybrid_method = method
        if method == "rrf":
            self._hybrid_k = kwargs.get("k", 60)
        else:
            raise ValueError(f"Unsupported hybrid method: {method}")
        return self

    def _execute_semantic_search(
        self,
        query: str | list[float],
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RetrievedChunk]:
        """Execute semantic search."""
        # Prepare embedding
        if isinstance(query, str):
            query_embedding = self.store.embed_query(query)[0]
        else:
            query_embedding = query

        # Build query args
        query_args = {"query_embedding": query_embedding}
        if limit is not None:
            query_args["limit"] = limit
        if offset is not None:
            query_args["offset"] = offset
        if self._filters is not None:
            query_args["filters"] = self._filters

        return self.store.db.semantic_search(**query_args)

    def _execute_keyword_search(
        self, query: str, limit: int | None = None, offset: int | None = None
    ) -> list[RetrievedChunk]:
        """Execute keyword search."""
        # Build query args
        query_args = {"query": query}
        if limit is not None:
            query_args["limit"] = limit
        if offset is not None:
            query_args["offset"] = offset
        if self._filters is not None:
            query_args["filters"] = self._filters

        return self.store.db.keyword_search(**query_args)

    def get(self) -> list[RetrievedChunk]:
        # Check if any query is set
        if self._semantic_query is None and self._keyword_query is None:
            raise ValueError(
                "No query set. Use .semantic() or .keyword() to set a query."
            )

        if self._semantic_query and self._keyword_query:
            limit = self._chunk_limit or 10
            offset = self._chunk_offset or 0
            fetch_limit = limit * 3 + offset  # Fetch 3x limit plus offset for RRF

            semantic_results = self._execute_semantic_search(
                self._semantic_query, limit=fetch_limit, offset=0
            )
            keyword_results = self._execute_keyword_search(
                self._keyword_query, limit=fetch_limit, offset=0
            )

            # Combine using RRF
            combined = combine_rrf(semantic_results, keyword_results, k=self._hybrid_k)

            # Apply final limit and offset
            end = offset + limit
            return combined[offset:end]

        # Single search mode
        if self._semantic_query:
            return self._execute_semantic_search(
                self._semantic_query, limit=self._chunk_limit, offset=self._chunk_offset
            )

        if self._keyword_query:
            return self._execute_keyword_search(
                self._keyword_query, limit=self._chunk_limit, offset=self._chunk_offset
            )

        # Should never reach here given the initial check
        return []

    def get_documents(self) -> list[T]:
        chunks = self.get()
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
        documents = self.store.db.get_documents_by_id(doc_ids)

        # Attach chunks to documents
        for doc in documents:
            doc.chunks = chunks_by_doc_id.get(doc.id, [])

        # Sort documents by minimum chunk distance
        documents.sort(key=lambda doc: min_distance_by_doc_id.get(doc.id, float("inf")))

        return documents


def combine_rrf(
    semantic_results: list[RetrievedChunk],
    keyword_results: list[RetrievedChunk],
    k: int = 60,
) -> list[RetrievedChunk]:
    """Combine search results using Reciprocal Rank Fusion.

    RRF(d) = Σ(r ∈ R) 1 / (k + r(d))

    Args:
        semantic_results: Results from semantic search (assumed to be rank-ordered)
        keyword_results: Results from keyword search (assumed to be rank-ordered)
        k: RRF constant (default 60, standard in literature)

    Returns:
        Combined and re-ranked results
    """
    # Calculate RRF scores
    rrf_scores = {}

    # Add scores from semantic search
    for rank, chunk in enumerate(semantic_results, 1):
        key = (chunk.document_id, chunk.chunk_idx)
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)

    # Add scores from keyword search
    for rank, chunk in enumerate(keyword_results, 1):
        key = (chunk.document_id, chunk.chunk_idx)
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)

    # Build a map of keys to chunks (preferring semantic results for metadata)
    chunk_map = {}
    for chunk in semantic_results:
        key = (chunk.document_id, chunk.chunk_idx)
        chunk_map[key] = chunk
    for chunk in keyword_results:
        key = (chunk.document_id, chunk.chunk_idx)
        if key not in chunk_map:
            chunk_map[key] = chunk

    # Sort by RRF score (higher is better) and rebuild results
    sorted_keys = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for key, score in sorted_keys:
        chunk = chunk_map[key]
        # Store RRF score as negative distance (so higher score = lower distance)
        chunk.distance = -score
        results.append(chunk)

    return results
