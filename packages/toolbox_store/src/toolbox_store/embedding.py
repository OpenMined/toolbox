import hashlib
import itertools
from functools import cached_property

from semantic_text_splitter import TextSplitter

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


class OllamaEmbedder:
    def __init__(
        self,
        model_name: str = "embeddinggemma:300m",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        batch_size: int = 8,
        ollama_url: str = "http://localhost:11434",
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.ollama_client = OllamaEmbeddingClient(ollama_url=ollama_url)
        self.splitter = TextSplitter(capacity=chunk_size, overlap=chunk_overlap)

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

    def embed(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
        prompt_type: str | None = None,
    ) -> list[list[float]]:
        self._setup()
        if isinstance(texts, str):
            texts = [texts]

        texts = self._format_with_prompt(texts, prompt_type)

        embeddings = []
        batch_size_ = batch_size or self.batch_size
        for batch in itertools.batched(texts, batch_size_):
            batch_embeddings = self.ollama_client.embed(self.model_name, batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def embed_document(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        return self.embed(texts, batch_size=batch_size, prompt_type="document")

    def embed_query(
        self,
        texts: str | list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        return self.embed(texts, batch_size=batch_size, prompt_type="query")

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
                    "content_hash": hashlib.sha256(chunk_content.encode()).hexdigest(),
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


if __name__ == "__main__":
    from pathlib import Path

    from toolbox_store.data_loaders import load_from_dir

    # Use same data directory as db.py
    data_dir = Path(__file__).parent.parent.parent / "experimental" / "data"
    print(f"Data directory: {data_dir.absolute()}")

    max_docs = 3  # Test with just a few documents
    docs = load_from_dir(data_dir, max_docs=max_docs)

    # Test embed_documents
    config = StoreConfig()
    embedder = OllamaEmbedder(
        model_name=config.embedding_model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    chunks = embedder.chunk_and_embed(docs)

    print(f"\nCreated {len(chunks)} embeddings")

    # Show some details about the first few embeddings
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nEmbedding {i}:")
        print(f"  - Document ID: {chunk.document_id}")
        print(f"  - Chunk index: {chunk.chunk_idx}")
        print(f"  - Chunk range: [{chunk.chunk_start}:{chunk.chunk_end}]")
        print(f"  - Content preview: {chunk.content[:100]}...")
        print(f"  - Embedding shape: {len(chunk.embedding)} dimensions")
        print(f"  - Content hash: {chunk.content_hash[:16]}...")
