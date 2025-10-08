import os
import sys
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omni.app import app
from omni.vectorstore_models import Tweet
from toolbox_store import ToolboxStore
from toolbox_store.models import StoreConfig

client = TestClient(app)


def create_mock_store():
    config = StoreConfig(embedding_model="random", embedding_dim=32)
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()

    store = ToolboxStore(
        "tweets", db_path=temp_file.name, config=config, document_class=Tweet
    )

    mock_tweets = [
        Tweet(
            id="1",
            tweet_id="123",
            content="coding aesthetics vibes music",
            author={
                "screen_name": "test",
                "name": "Test",
                "avatar_url": "https://example.com/test.jpg",
            },
            created_at_tweet="2025-08-01T10:30:00Z",
            favorite_count=10,
            retweet_count=5,
            lang="en",
            source="test",
        ),
        Tweet(
            id="2",
            tweet_id="456",
            content="programming beautiful code vibes",
            author={
                "screen_name": "dev",
                "name": "Dev",
                "avatar_url": "https://example.com/dev.jpg",
            },
            created_at_tweet="2025-08-15T14:20:00Z",
            favorite_count=20,
            retweet_count=3,
            lang="en",
            source="test",
        ),
    ]

    store.insert_docs(mock_tweets, create_embeddings=True)
    return store


def test_twitter_smart_list_items():
    with patch(
        "omni.vectorstore_queries.get_tweet_store", side_effect=create_mock_store
    ):
        response = client.get("/smart-lists")
        smart_lists = response.json()

        twitter_list = next(
            (
                sl
                for sl in smart_lists
                if any(
                    s.get("dataSourceId") == "twitter"
                    for s in sl.get("listSources", [])
                )
            ),
            None,
        )

        assert twitter_list is not None

        response = client.get(f"/smart-lists/{twitter_list['id']}/items")
        items = response.json()

        assert len(items) > 1
        assert all(item.get("similarity_score", 0) > 0 for item in items)

        # Verify frontend-expected JSON structure
        for item in items:
            assert "id" in item
            assert "type" in item
            assert item["type"] == "tweet"
            assert "content" in item
            assert "author" in item
            assert "name" in item["author"]
            assert "handle" in item["author"]
            assert item["author"]["handle"].startswith("@")
            assert "avatarUrl" in item["author"]
            assert "likes" in item
            assert "reactions" in item
            assert "timestamp" in item


if __name__ == "__main__":
    test_twitter_smart_list_items()
    print("✅ Test passed!")
