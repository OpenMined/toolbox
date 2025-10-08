import warnings
from typing import Any, cast

from rerankers import Reranker

from toolbox_store.models import RetrievedChunk

warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*Failed to initialize NumPy.*")
warnings.filterwarnings(
    "ignore", message=".*A module that was compiled using NumPy 1.x cannot be *"
)

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

    # Suppress ColBERT loading messages by setting verbose=0
    if model_type == "colbert" and "verbose" not in model_kwargs:
        model_kwargs["verbose"] = 0

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
        chunk = chunks_by_id[(doc_id, chunk_idx)]
        chunk.score = res.score if res.score is not None else -1
        reranked_chunks.append(chunk)

    return reranked_chunks


# def _get_normalize_bounds(
#     reranker: BaseRanker,
#     results: list[RetrievedChunk],
#     query: str,
# ) -> tuple[float, float]:
#     min_score = np.inf
#     max_score = -np.inf
#     all_scores = [-res.distance for res in results if res.distance is not None]
#     if all_scores:
#         min_score = min(all_scores)
#         max_score = max(all_scores)

#     bounds_ranked = reranker.rank(
#         query=query,
#         docs=[DUMMY_DOC, query],
#         doc_ids=[0, 1],
#     ).results

#     bounds = [min_score, max_score]
#     for res in bounds_ranked:
#         if res.score is not None:
#             bounds[0] = min(bounds[0], res.score)
#             bounds[1] = max(bounds[1], res.score)

#     return bounds[0], bounds[1]


# def _normalize(
#     chunks: list[RetrievedChunk], min_val: float = 0.0, max_val: float = 1.0
# ) -> list[RetrievedChunk]:
#     """Normalize chunk distances to a specified range [min_val, max_val]."""
#     if not chunks:
#         return chunks

#     distances = [chunk.distance for chunk in chunks if chunk.distance is not None]
#     if not distances:
#         return chunks

#     min_score, max_score = min(distances), max(distances)

#     if min_distance == max_distance:
#         for chunk in chunks:
#             chunk.distance = (min_val + max_val) / 2.0
#         return chunks

#     for chunk in chunks:
#         if chunk.distance is not None:
#             normalized_score = (chunk.distance - min_distance) / (
#                 max_distance - min_distance
#             )
#             chunk.distance = normalized_score * (max_val - min_val) + min_val

#     return chunks
