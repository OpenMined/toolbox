from toolbox_store import TBDocument, ToolboxStore


def test_semantic_search(tb_store: ToolboxStore, sample_docs: list[TBDocument]) -> None:
    """Test inserting documents and creating embeddings"""
    tb_store.insert_docs(sample_docs, create_embeddings=True)

    all_docs = tb_store.search_documents().get()
    assert len(all_docs) == len(sample_docs)

    retrieved = tb_store.search_chunks().semantic("test").chunk_limit(5).get()
    assert len(retrieved) == 5
    assert retrieved[0].embedding is not None

    # Test semantic search with filters
    sample_docs[0].metadata["category"] = "category1"
    tb_store.insert_docs([sample_docs[0]], create_embeddings=False, overwrite=True)

    results_with_filter = (
        tb_store.search_chunks()
        .semantic("test")
        .where({"metadata.category": "category1"})
        .chunk_limit(5)
        .get_documents()
    )
    assert len(results_with_filter)
    for res in results_with_filter:
        assert res.metadata.get("category") == "category1"


# def test_keyword_search(
#     tb_store: ToolboxStore[TBDocument], sample_docs: list[TBDocument]
# ) -> None:
#     """Test keyword search"""
#     sample_docs[0].content = "This is a sample document about Python."
#     tb_store.insert_docs(sample_docs, create_embeddings=True)

#     # Simple keyword search
#     results = tb_store.search_chunks().keyword("sample").chunk_limit(10).get()
#     assert len(results) > 0
#     for res in results:
#         assert "sample" in res.content.lower()

#     # Keyword search with filters
#     sample_docs[0].metadata["category"] = "category1"
#     tb_store.insert_docs([sample_docs[0]], create_embeddings=False)

#     results_with_filter = (
#         tb_store.search_chunks()
#         .keyword("sample")
#         .where({"metadata.category": "category1"})
#         .chunk_limit(10)
#         .get_documents()
#     )
#     assert len(results_with_filter) > 0
#     for res in results_with_filter:
#         assert "sample" in res.content.lower()
#         assert res.metadata.get("category") == "category1"


def test_hybrid_search(
    tb_store: ToolboxStore[TBDocument], sample_docs: list[TBDocument]
) -> None:
    """Test hybrid search (semantic + keyword)"""
    sample_docs[0].content = "This is a sample document about Python."
    tb_store.insert_docs(sample_docs, create_embeddings=True)

    results = (
        tb_store.search_chunks()
        .semantic("Documents about python")
        .keyword("sample")
        .chunk_limit(10)
        .get()
    )
    assert len(results) > 0
