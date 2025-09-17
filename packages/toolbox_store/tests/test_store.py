from datetime import datetime

from toolbox_store import TBDocument, ToolboxStore
from toolbox_store.models import StoreConfig


def test_insert_documents_and_count(
    tb_store: ToolboxStore, sample_docs: list[TBDocument]
) -> None:
    """Test that documents are inserted and we can get the count"""
    tb_store.insert_docs(sample_docs, create_embeddings=False)

    all_docs = tb_store.search_documents().get()
    assert len(all_docs) == len(sample_docs)


def test_query_documents_with_filters(
    tb_store: ToolboxStore, sample_docs: list[TBDocument]
) -> None:
    """Test querying documents with filters"""
    sample_docs[0].metadata["category"] = "category1"
    sample_docs[1].metadata["category"] = "category2"

    sample_docs[0].metadata["num_downloads"] = 100
    sample_docs[1].metadata["num_downloads"] = 200

    tb_store.insert_docs(sample_docs, create_embeddings=False)

    # test eq
    results_1 = (
        tb_store.search_documents().where({"metadata.category": "category1"}).get()
    )
    assert len(results_1) == 1
    assert results_1[0].metadata["category"] == "category1"

    results_2 = (
        tb_store.search_documents().where({"metadata.category": "category2"}).get()
    )
    assert len(results_2) == 1
    assert results_2[0].metadata["category"] == "category2"

    # test gt, lt, gte, lte
    results_3 = (
        tb_store.search_documents().where({"metadata.num_downloads__gt": 150}).get()
    )
    assert len(results_3) == 1
    assert results_3[0].metadata["num_downloads"] == 200
    results_4 = (
        tb_store.search_documents().where({"metadata.num_downloads__lt": 150}).get()
    )
    assert len(results_4) == 1
    assert results_4[0].metadata["num_downloads"] == 100
    results_5 = (
        tb_store.search_documents().where({"metadata.num_downloads__gte": 200}).get()
    )
    assert len(results_5) == 1
    assert results_5[0].metadata["num_downloads"] == 200
    results_6 = (
        tb_store.search_documents().where({"metadata.num_downloads__lte": 100}).get()
    )
    assert len(results_6) == 1
    assert results_6[0].metadata["num_downloads"] == 100

    # test IN, CONTAINS
    results_7 = (
        tb_store.search_documents()
        .where({"metadata.category__in": ["category1", "category3"]})
        .get()
    )
    assert len(results_7) == 1
    assert results_7[0].metadata["category"] == "category1"
    results_8 = (
        tb_store.search_documents()
        .where({"metadata.category__contains": "category"})
        .get()
    )
    assert len(results_8) == 2
    assert set(doc.metadata["category"] for doc in results_8) == {
        "category1",
        "category2",
    }

    # test eq null, isnull
    results_9 = tb_store.search_documents().where({"metadata.category": None}).get()
    assert len(results_9) == len(sample_docs) - 2
    results_10 = (
        tb_store.search_documents().where({"metadata.nonexistent__isnull": True}).get()
    )
    assert len(results_10) == len(sample_docs)


def test_custom_doc_cls(tb_config: StoreConfig) -> None:
    class Message(TBDocument):
        author: str = "default_value"
        date_received: datetime

        @classmethod
        def schema_extra_columns(cls) -> list[tuple[str, str]]:
            return [
                ("author", "TEXT"),
                ("date_received", "DATETIME"),
            ]

        @classmethod
        def schema_extra(
            cls,
            documents_table: str,
            *args: str,
        ) -> list[str]:
            return [
                f"CREATE INDEX IF NOT EXISTS idx_{documents_table}_date_received ON {documents_table} (date_received)",
            ]

    store = ToolboxStore(
        "messages",
        db_path=":memory:",
        config=tb_config,
        document_class=Message,
    )

    messages = [
        Message(
            id="msg1",
            content="Hello, this is a test message.",
            author="Alice",
            date_received=datetime(2024, 7, 16),
            source="message",
        ),
        Message(
            id="msg2",
            content="Another message for testing.",
            author="Bob",
            date_received=datetime(2025, 7, 15),
            source="message",
        ),
        Message(
            id="msg3",
            content="This message is from Charlie.",
            author="Charlie",
            date_received=datetime(2025, 7, 16),
            source="message",
        ),
    ]

    store.insert_docs(messages, create_embeddings=False)

    all_msgs = store.search_documents().where({"author": "Alice"}).get()
    assert len(all_msgs) == 1
    assert all_msgs[0].author == "Alice"

    date_filtered = (
        store.search_documents()
        .where({"date_received__gte": datetime(2025, 7, 1)})
        .where({"date_received__lt": datetime(2026, 8, 1)})
        .order_by("date_received", ascending=True)
        .get()
    )
    assert len(date_filtered) == 2
    assert date_filtered[0].author == "Bob"
    assert date_filtered[1].author == "Charlie"
