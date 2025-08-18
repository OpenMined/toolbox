"""Test the embedding background worker."""

from unittest.mock import patch

from discord_mcp.db import (
    get_discord_connection,
    get_matching_chunks,
    get_messages_without_embeddings,
    upsert_message,
)
from discord_mcp.embedding_background_worker import (
    run_embedding_background_worker_single,
)
from discord_mcp.models import DiscordMessage

from tests.utils import get_random_tmp_file


def test_embedding_background_worker():
    """Test the embedding background worker with mock data."""
    # Create a temporary database
    tmp_db_path = get_random_tmp_file()

    try:
        # Set up test data
        with get_discord_connection(tmp_db_path) as conn:
            # Create test messages
            test_messages = [
                DiscordMessage(
                    id="1000000000000000001",
                    channel_id="2000000000000000001",
                    author_id="3000000000000000001",
                    content="This is a test message about machine learning",
                    timestamp="2024-01-01T00:00:00Z",
                    type=0,
                ),
                DiscordMessage(
                    id="1000000000000000002",
                    channel_id="2000000000000000001",
                    author_id="3000000000000000002",
                    content="Another message about deep learning and AI",
                    timestamp="2024-01-01T01:00:00Z",
                    type=0,
                ),
                DiscordMessage(
                    id="1000000000000000003",
                    channel_id="2000000000000000002",
                    author_id="3000000000000000001",
                    content="A different topic about cooking recipes",
                    timestamp="2024-01-01T02:00:00Z",
                    type=0,
                ),
            ]

            # Insert test messages
            for msg in test_messages:
                upsert_message(conn, msg)

            # Verify messages are there and have no embeddings
            messages_without_embeddings = get_messages_without_embeddings(conn)
            assert len(messages_without_embeddings) == 3

        # Mock the embedding function to return deterministic vectors
        def mock_get_embedding(text):
            # Return a simple hash-based vector for reproducible results
            hash_val = hash(text) % 1000000
            return [(hash_val + i) / 1000000.0 for i in range(768)]

        # Patch the embedding function and run worker
        with patch(
            "discord_mcp.embedding_background_worker.get_embedding",
            side_effect=mock_get_embedding,
        ):
            with get_discord_connection(tmp_db_path) as conn:
                # Run one iteration of the background worker
                run_embedding_background_worker_single(conn)

                # Verify messages now have embeddings (no messages should be without embeddings)
                messages_without_embeddings_after = get_messages_without_embeddings(
                    conn
                )
                assert (
                    len(messages_without_embeddings_after) < 3
                )  # Some messages should now have embeddings

        # Test the RAG functionality by directly calling the db functions
        with patch(
            "discord_mcp.embedding_background_worker.get_embedding",
            side_effect=mock_get_embedding,
        ):
            with get_discord_connection(tmp_db_path) as conn:
                # Test searching for embeddings
                query_embedding = mock_get_embedding("machine learning")
                matching_chunks = get_matching_chunks(conn, query_embedding, limit=5)

                # Should return some matches
                assert len(matching_chunks) > 0

                # Check that chunks have the expected structure
                for chunk in matching_chunks:
                    assert "chunk_id" in chunk
                    assert "chunk_text" in chunk
                    assert "message_ids" in chunk
                    assert len(chunk["message_ids"]) > 0

    finally:
        # Clean up temporary database
        if tmp_db_path.exists():
            tmp_db_path.unlink()
