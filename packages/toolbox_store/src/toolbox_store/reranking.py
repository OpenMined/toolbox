from typing import Any, cast

from rerankers import Reranker

from toolbox_store.models import RetrievedChunk

loaded_rerankers: dict[(str, str), Reranker] = {}

DEFAULT_RERANKER_MODEL = "answerdotai/answerai-colbert-small-v1"
DEFAULT_RERANKER_TYPE = "colbert"


def load_reranker(
    model_name: str = DEFAULT_RERANKER_MODEL,
    model_type: str = DEFAULT_RERANKER_TYPE,
    **model_kwargs: Any,
) -> Any:
    """Create a reranker instance if rerankers library is available."""

    if (model_name, model_type) in loaded_rerankers:
        return loaded_rerankers[(model_name, model_type)]
    reranker = Reranker(model_name, model_type=model_type, **model_kwargs)
    loaded_rerankers[(model_name, model_type)] = reranker
    return reranker


def rerank_chunks(
    chunks: list[RetrievedChunk],
    query: str,
    model_name: str = DEFAULT_RERANKER_MODEL,
    model_type: str = DEFAULT_RERANKER_TYPE,
    **model_kwargs: Any,
) -> list[RetrievedChunk]:
    """Rerank retrieved chunks using a specified reranker model."""

    from rerankers.results import RankedResults

    reranker = load_reranker(model_name, model_type, **model_kwargs)

    docs = [chunk.content for chunk in chunks]
    metadatas = [
        {"document_id": chunk.document_id, "chunk_idx": chunk.chunk_idx}
        for chunk in chunks
    ]
    reranked = reranker.rank(query=query, docs=docs, metadata=metadatas)
    reranked = cast(RankedResults, reranked)

    chunks_by_id = {(chunk.document_id, chunk.chunk_idx): chunk for chunk in chunks}

    reranked_chunks = []
    for res in reranked.results:
        doc_id = res.document.metadata["document_id"]
        chunk_idx = res.document.metadata["chunk_idx"]
        score = res.score if res.score is not None else 0.0
        distance = -score
        chunk = chunks_by_id[(doc_id, chunk_idx)]
        chunk.distance = distance
        reranked_chunks.append(chunk)

    return reranked_chunks
