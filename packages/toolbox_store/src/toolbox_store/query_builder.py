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

        self._order_by: str = "id"
        self._sort_ascending: bool = True

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

    def order_by(self, field: str, ascending: bool = True) -> Self:
        self._order_by = field
        self._sort_ascending = ascending
        return self

    def get(self) -> list[T]:
        """Execute the query and return documents."""
        return self.store.db.get_documents(
            filters=self._filters,
            limit=self._limit,
            offset=self._offset,
            order_by=self._order_by,
            sort_ascending=self._sort_ascending,
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

        # Hybrid search parameters
        self._hybrid_method: str = "rrf"
        self._hybrid_k: int = 60
        self._semantic_weight: float = 1.0
        self._keyword_weight: float = 1.0

        self._rerank_query: str | None = None
        self._rerank_model_name: str | None = None
        self._rerank_model_type: str | None = None
        self._rerank_model_kwargs: dict[str, Any] | None = None

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

    def hybrid(
        self,
        method: str = "rrf",
        *,
        k: int = 60,
        semantic_weight: float = 1.0,
        keyword_weight: float = 1.0,
    ) -> Self:
        """Configure hybrid search method.

        Args:
            method: Currently only 'rrf' (Reciprocal Rank Fusion) is supported
            k: RRF constant (default 60, standard in literature)
            semantic_weight: Weight for semantic results (default 1.0)
            keyword_weight: Weight for keyword results (default 1.0)

        Returns:
            Self for chaining
        """
        self._hybrid_method = method
        if method == "rrf":
            self._hybrid_k = k
            self._semantic_weight = semantic_weight
            self._keyword_weight = keyword_weight
        else:
            raise ValueError(f"Unsupported hybrid method: {method}")
        return self

    def rerank(
        self,
        rerank_query: str | None = None,
        model_name: str = "answerdotai/answerai-colbert-small-v1",
        model_type: str = "colbert",
        **model_kwargs: Any,
    ) -> Self:
        """Rerank the final chunks using a specified reranker model."""
        if rerank_query is None:
            if not isinstance(self._semantic_query, str):
                raise ValueError(
                    "Rerank query must be provided if semantic query is not a string."
                )
            rerank_query = self._semantic_query

        self._rerank_query = rerank_query
        self._rerank_model_name = model_name
        self._rerank_model_type = model_type
        self._rerank_model_kwargs = model_kwargs
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
            combined = combine_rrf(
                semantic_results,
                keyword_results,
                weights=[self._semantic_weight, self._keyword_weight],
                k=self._hybrid_k,
            )

            # Apply final limit and offset
            end = offset + limit
            chunks = combined[offset:end]

        # Single search mode
        elif self._semantic_query:
            chunks = self._execute_semantic_search(
                self._semantic_query, limit=self._chunk_limit, offset=self._chunk_offset
            )

        elif self._keyword_query:
            chunks = self._execute_keyword_search(
                self._keyword_query, limit=self._chunk_limit, offset=self._chunk_offset
            )

        else:
            chunks = []

        if self._rerank_query is not None and len(chunks) > 0:
            from toolbox_store.reranking import rerank_chunks

            chunks = rerank_chunks(
                chunks,
                query=self._rerank_query,
                model_name=self._rerank_model_name,
                model_type=self._rerank_model_type,
                **(self._rerank_model_kwargs or {}),
            )

        return chunks

    def get_documents(self) -> list[T]:
        chunks = self.get()
        chunks_by_doc_id = {}
        max_score_by_doc_id = {}

        # Group chunks by document and track maximum score
        for chunk in chunks:
            if chunk.document_id not in chunks_by_doc_id:
                chunks_by_doc_id[chunk.document_id] = []
                max_score_by_doc_id[chunk.document_id] = chunk.score
            chunks_by_doc_id[chunk.document_id].append(chunk)
            max_score_by_doc_id[chunk.document_id] = max(
                max_score_by_doc_id[chunk.document_id], chunk.score
            )

        # Get documents from database
        doc_ids = list(chunks_by_doc_id.keys())
        documents = self.store.db.get_documents_by_id(doc_ids)

        # Attach chunks to documents
        for doc in documents:
            doc.chunks = chunks_by_doc_id.get(doc.id, [])

        # Sort documents by maximum chunk score (descending)
        documents.sort(
            key=lambda doc: max_score_by_doc_id.get(doc.id, float("-inf")), reverse=True
        )

        return documents


def combine_rrf(
    *result_sets: list[RetrievedChunk],
    weights: list[float] | None = None,
    k: int = 60,
) -> list[RetrievedChunk]:
    """Combine multiple search result sets using weighted Reciprocal Rank Fusion.

    RRF(d) = Σ(r ∈ R) weight_r * (1 / (k + rank_r(d)))

    Args:
        *result_sets: Variable number of search result lists (each assumed to be rank-ordered)
        weights: Optional weights for each result set (defaults to equal weights)
        k: RRF constant (default 60, standard in literature)

    Returns:
        Combined and re-ranked results
    """
    if not result_sets:
        return []

    # Use equal weights if not provided
    if weights is None:
        weights = [1.0] * len(result_sets)

    if len(weights) != len(result_sets):
        raise ValueError(
            f"Number of weights ({len(weights)}) must match number of result sets ({len(result_sets)})"
        )

    # Calculate RRF scores
    rrf_scores: dict[tuple[str, int], float] = {}

    # Add weighted scores from each result set
    for weight, results in zip(weights, result_sets):
        for rank, chunk in enumerate(results, 1):
            key = (chunk.document_id, chunk.chunk_idx)
            rrf_scores[key] = rrf_scores.get(key, 0) + weight * (1 / (k + rank))

    # Build a map of keys to chunks (first occurrence wins)
    chunk_map: dict[tuple[str, int], RetrievedChunk] = {}
    for results in result_sets:
        for chunk in results:
            key = (chunk.document_id, chunk.chunk_idx)
            if key not in chunk_map:
                chunk_map[key] = chunk

    # Sort by RRF score (higher is better) and rebuild results
    sorted_keys = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for key, score in sorted_keys:
        chunk = chunk_map[key]
        # Store RRF score as negative distance (so higher score = lower distance)
        chunk.score = score
        results.append(chunk)

    return results
