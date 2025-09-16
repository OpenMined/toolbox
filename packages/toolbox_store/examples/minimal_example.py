# %%
# from datetime import datetime
from datetime import datetime
from pathlib import Path

from toolbox_store.data_loaders import load_from_dir
from toolbox_store.models import TBDocument
from toolbox_store.store import ToolboxStore

DATA_DIR = Path(__file__).parent / "fineweb-bbc-news"
db_path = DATA_DIR / "example.db"

documents: list[TBDocument] = load_from_dir(DATA_DIR, max_docs=10)
store = ToolboxStore("my_collection", db_path=db_path, reset=True)
print(len(documents), "documents loaded from", DATA_DIR)

print([doc.metadata.get("filename") for doc in documents])
store.insert_docs(
    documents,
    create_embeddings=True,
)

# %%
query = (
    store.search_chunks()
    .semantic("Airport security")
    .where({"created_at__gte": datetime(2025, 9, 1)})
    .where({"created_at__lt": datetime(2025, 10, 1)})
    # .keyword("history AI") # TODO sqlite fts index
    # .hybrid(semantic_weight=0.8) # TODO linear combination of fts + semantic
    # .rerank() # TODO reranker support
    .chunk_limit(10)
)

chunks = query.get()
print(f"Retrieved {len(chunks)} chunks")

for chunk in chunks:
    print(f"- Chunk (doc {chunk.document_id}, dist {chunk.distance:.4f}):")
    print(f"  {chunk.content[:200]}...")
    print()
# %%

docs = query.get_documents()
print(f"Retrieved {len(docs)} documents")

for doc in docs:
    print(f"- Document {doc.id} (metadata: {doc.metadata}):")
    print(f"  {doc.content[:200]}...")
    print(f"  num retrieved chunks: {len(doc.chunks)}")
    print(f"  min distance: {doc.chunks[0].distance if doc.chunks else 'N/A'}")
    print()

# %%
query = (
    store.search_chunks()
    .keyword("yates")
    .where({"metadata.filename__contains": "001"})
    .chunk_limit(10)
)

docs = query.get_documents()
print(f"Retrieved {len(docs)} documents")

for doc in docs:
    print(f"- Document {doc.id} (metadata: {doc.metadata}):")
    print(f"  {doc.content[:200]}...")
    print(f"  num retrieved chunks: {len(doc.chunks)}")
    print(f"  min distance: {doc.chunks[0].distance if doc.chunks else 'N/A'}")
    print()

# %%

query = (
    store.search_chunks()
    .semantic("airport security")  # vector similarity
    .keyword("yates")  # bm25
    .hybrid(method="rrf")  # fuse semantic + keyword scores
    .where(
        {
            "metadata.filename__contains": "001",  # django-style operators
            "created_at__gte": datetime(2025, 9, 1),  # datetimes are converted to str
        }
    )
    .chunk_limit(10)
)

docs = query.get_documents()
print(f"Retrieved {len(docs)} documents")
for doc in docs:
    print(f"- Document {doc.id} (metadata: {doc.metadata}):")
    print(f"  {doc.content[:500]}...")
    print(f"  num retrieved chunks: {len(doc.chunks)}")
    print(f"  min distance: {doc.chunks[0].distance if doc.chunks else 'N/A'}")
    print()

# %%
