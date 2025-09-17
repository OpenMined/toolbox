from pathlib import Path

import pytest
from toolbox_store import TBDocument, ToolboxStore
from toolbox_store.data_loaders import load_from_dir
from toolbox_store.models import StoreConfig

ASSETS_DIR = Path(__file__).parent / "assets"
TEST_DATA_DIR = ASSETS_DIR / "data"


@pytest.fixture
def tb_config() -> StoreConfig:
    return StoreConfig(
        embedding_model="random",
        embedding_dim=32,
        chunk_size=50,
        chunk_overlap=10,
        batch_size=8,
    )


@pytest.fixture
def tb_store(tb_config: StoreConfig) -> ToolboxStore:
    """In-memory store with mocked embeddings"""
    return ToolboxStore("test", db_path=":memory:", config=tb_config)


@pytest.fixture
def sample_docs() -> list[TBDocument]:
    return load_from_dir(TEST_DATA_DIR)
