from typing import Generic, TypeVar, overload

from toolbox_store.models import ToolboxDocument, ToolboxEmbedding

T = TypeVar("T", bound=ToolboxDocument)


class ToolboxStore(Generic[T]):
    @overload
    def __init__(self, collection: str, model: type[T]) -> None: ...

    @overload
    def __init__(
        self: "ToolboxStore[ToolboxDocument]", collection: str, model: None = None
    ) -> None: ...

    def __init__(self, collection: str, model: type[T] | None = None) -> None:
        self.collection = collection
        self.model = model or ToolboxDocument

    def insert_docs(self, docs: list[T], embed_immediately: bool = True) -> None:
        pass

    def insert_embeddings(self, embeddings: list[ToolboxEmbedding]) -> None:
        pass

    def embed_batch(self, docs: list[T]) -> list[ToolboxEmbedding]:
        pass

    def search(self) -> "SearchQueryBuilder[T]":
        return SearchQueryBuilder(self, self.model)


class SearchQueryBuilder(Generic[T]):
    def __init__(self, store: "ToolboxStore[T]", model: type[T]):
        self.store = store
        self.model = model

    def semantic(self, query: str) -> "SearchQueryBuilder[T]":
        return self

    def filter(self, filters: dict) -> "SearchQueryBuilder[T]":
        return self

    def limit(self, n: int) -> "SearchQueryBuilder[T]":
        return self

    def offset(self, n: int) -> "SearchQueryBuilder[T]":
        return self

    def to_pydantic(self) -> list[T]:
        return []
