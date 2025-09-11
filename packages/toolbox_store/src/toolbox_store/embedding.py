# %%
import hashlib

import fastembed
from semantic_text_splitter import TextSplitter

from toolbox_store.models import StoreConfig, ToolboxDocument, ToolboxEmbedding


def get_fastembed_model(config: StoreConfig) -> fastembed.TextEmbedding:
    return fastembed.TextEmbedding(model_name=config.embedding_model)


def embed_documents(
    documents: list[ToolboxDocument],
    config: StoreConfig,
    model: fastembed.TextEmbedding | None = None,
) -> list[ToolboxEmbedding]:
    if model is None:
        model = get_fastembed_model(config)

    text_splitter = TextSplitter(
        capacity=config.chunk_size, overlap=config.chunk_overlap
    )

    texts_chunked = text_splitter.chunk_all_indices(
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

    chunk_contents = [chunk["content"] for chunk in chunks_with_metadata]
    embeddings = model.embed(chunk_contents, batch_size=config.batch_size)
    for chunk_metadata, embedding in zip(chunks_with_metadata, embeddings):
        chunk_metadata["embedding"] = embedding.tolist()

    return [
        ToolboxEmbedding.model_validate(chunk_metadata)
        for chunk_metadata in chunks_with_metadata
    ]


if __name__ == "__main__":
    from datetime import datetime, timezone
    from pathlib import Path

    from toolbox_store.models import ToolboxDocument

    # Use same data directory as db.py
    data_dir = Path(__file__).parent.parent.parent / "data"
    print(f"Data directory: {data_dir.absolute()}")

    max_docs = 3  # Test with just a few documents
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

    print(f"\nLoaded {len(docs_to_insert)} documents to embed")

    # Test embed_documents
    config = StoreConfig()
    print("\nUsing config:")
    print(f"  - Embedding model: {config.embedding_model}")
    print(f"  - Embedding dimensions: {config.embedding_dim}")
    print(f"  - Chunk size: {config.chunk_size}")
    print(f"  - Chunk overlap: {config.chunk_overlap}")

    embeddings = embed_documents(docs_to_insert, config)

    print(f"\nCreated {len(embeddings)} embeddings")

    # Show some details about the first few embeddings
    for i, emb in enumerate(embeddings[:5]):
        print(f"\nEmbedding {i}:")
        print(f"  - Document ID: {emb.document_id}")
        print(f"  - Chunk index: {emb.chunk_idx}")
        print(f"  - Chunk range: [{emb.chunk_start}:{emb.chunk_end}]")
        print(f"  - Content preview: {emb.content[:100]}...")
        print(f"  - Embedding shape: {len(emb.embedding)} dimensions")
        print(f"  - Content hash: {emb.content_hash[:16]}...")
