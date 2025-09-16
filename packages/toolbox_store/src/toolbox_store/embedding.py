import itertools
from abc import ABC, abstractmethod
from functools import cached_property

from semantic_text_splitter import TextSplitter
from tqdm import tqdm

from toolbox_store.models import StoreConfig, TBDocument, TBDocumentChunk
from toolbox_store.ollama_client import OllamaEmbeddingClient

# embeddinggemma has instruct prompts for different tasks
# Source: https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers
PROMPTS: dict[str, dict[str, str]] = {
    "embeddinggemma": {
        "query": "task: search result | query: ",
        "document": "title: none | text: ",
        "bitextmining": "task: search result | query: ",
        "clustering": "task: clustering | query: ",
        "classification": "task: classification | query: ",
        "instructionretrieval": "task: code retrieval | query: ",
        "multilabelclassification": "task: classification | query: ",
        "pairclassification": "task: sentence similarity | query: ",
        "reranking": "task: search result | query: ",
        "retrieval": "task: search result | query: ",
        "retrieval-query": "task: search result | query: ",
        "retrieval-document": "title: none | text: ",
        "sts": "task: sentence similarity | query: ",
        "summarization": "task: summarization | query: ",
    }
}


class Embedder(ABC):
    """Base class for all embedders with shared functionality."""

    def __init__(
        self,
        model_name: str = "base",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 8,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.splitter = TextSplitter(capacity=chunk_size, overlap=chunk_overlap)

    @cached_property
    def base_model_name(self) -> str:
        return self.model_name.split(":")[0]

    def _format_with_prompt(
        self, texts: list[str], prompt_type: str | None = None
    ) -> list[str]:
        if prompt_type is None:
            return texts

        if self.base_model_name not in PROMPTS:
            return texts

        model_prompts = PROMPTS[self.base_model_name]
        prompt_template = model_prompts.get(prompt_type, None)
        if prompt_template is None:
            return texts

        return [f"{prompt_template}{text}" for text in texts]

    @abstractmethod
    def _embed(self, batch: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        pass

    def embed(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
        prompt_type: str | None = None,
        show_progress: bool = True,
    ) -> list[list[float]]:
        """Generate embeddings for the given texts."""
        if isinstance(texts, str):
            texts = [texts]

        texts = self._format_with_prompt(texts, prompt_type)

        embeddings = []
        batch_size_ = batch_size or self.batch_size
        iterator = itertools.batched(texts, batch_size_)
        if show_progress:
            iterator = tqdm(
                iterator, total=(len(texts) + batch_size_ - 1) // batch_size_
            )
        for batch in iterator:
            batch_embeddings = self._embed(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def embed_document(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        return self.embed(
            texts, batch_size=batch_size, prompt_type="document", show_progress=True
        )

    def embed_query(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        return self.embed(
            texts, batch_size=batch_size, prompt_type="query", show_progress=False
        )

    def chunk(self, documents: list[TBDocument]) -> list[dict]:
        """Chunk documents into smaller pieces with metadata."""
        texts_chunked = self.splitter.chunk_all_indices(
            [document.content for document in documents]
        )

        chunks_with_metadata = []
        for doc, chunks in zip(documents, texts_chunked):
            for idx, (start, chunk_content) in enumerate(chunks):
                chunk = {
                    "document_id": doc.id,
                    "chunk_idx": idx,
                    "chunk_start": start,
                    "chunk_end": start + len(chunk_content),
                    "content": chunk_content,
                }
                chunks_with_metadata.append(chunk)

        return chunks_with_metadata

    def chunk_and_embed(self, documents: list[TBDocument]) -> list[TBDocumentChunk]:
        """Chunk documents and generate embeddings for each chunk."""
        chunks_with_metadata = self.chunk(documents)

        chunk_contents = [chunk["content"] for chunk in chunks_with_metadata]
        embeddings = self.embed_document(chunk_contents)

        for chunk_metadata, embedding in zip(chunks_with_metadata, embeddings):
            chunk_metadata["embedding"] = embedding

        return [
            TBDocumentChunk.model_validate(chunk_metadata)
            for chunk_metadata in chunks_with_metadata
        ]


class OllamaEmbedder(Embedder):
    def __init__(
        self,
        model_name: str = "embeddinggemma:300m",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 8,
        ollama_url: str = "http://localhost:11434",
    ):
        super().__init__(model_name, chunk_size, chunk_overlap, batch_size)
        self.ollama_client = OllamaEmbeddingClient(ollama_url=ollama_url)

    def _setup(self):
        try:
            if not self.ollama_client.model_exists(self.model_name):
                print(
                    f"Model '{self.model_name}' not found locally. Pulling from Ollama..."
                )
                self.ollama_client.pull(self.model_name, show_updates=True)
        except Exception as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.ollama_client.ollama_url}. "
                f"Make sure Ollama is running and accessible. Error: {e}"
            ) from e

    def _embed(self, batch: list[str]) -> list[list[float]]:
        self._setup()
        return self.ollama_client.embed(self.model_name, batch)


class RandomEmbedder(Embedder):
    """Mock embedder that returns random embeddings for testing."""

    def __init__(
        self,
        model_name: str = "mock",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 8,
        embedding_dim: int = 768,
    ):
        super().__init__(model_name, chunk_size, chunk_overlap, batch_size)
        self.embedding_dim = embedding_dim

    def _embed(self, batch: list[str]) -> list[list[float]]:
        import numpy as np

        n = len(batch)
        embeddings = np.random.random((n, self.embedding_dim))
        return embeddings.tolist()


def get_embedder(config: StoreConfig) -> Embedder:
    if config.embedding_model == "random":
        return RandomEmbedder(
            model_name="random",
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            batch_size=config.batch_size,
            embedding_dim=config.embedding_dim,
        )
    else:
        return OllamaEmbedder(
            model_name=config.embedding_model,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            batch_size=config.batch_size,
            ollama_url=config.ollama_url,
        )
