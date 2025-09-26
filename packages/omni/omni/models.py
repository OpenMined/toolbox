from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class DataSource(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    installCommand: str
    defaultUrl: str
    connectionState: str
    dashboardData: Dict


class DataCollection(BaseModel):
    id: str
    name: str
    items: List


# Database schema models (1:1 with database tables)
class SmartListDB(BaseModel):
    id: int
    name: str
    item_count: int
    created_at: str
    user_email: str

    @classmethod
    def from_sql_row(cls, row):
        """Create SmartListDB instance from SQLite row"""
        return cls(
            id=row["id"],
            name=row["name"],
            item_count=row["item_count"],
            created_at=row["created_at"],
            user_email=row["user_email"],
        )


class ListSourceDB(BaseModel):
    id: int
    list_id: int
    data_source_id: str

    @classmethod
    def from_sql_row(cls, row):
        """Create ListSourceDB instance from SQLite row"""
        return cls(
            id=row["id"], list_id=row["list_id"], data_source_id=row["data_source_id"]
        )


class ListFilterDB(BaseModel):
    id: int
    list_source_id: int
    date_range_from: Optional[str] = None
    date_range_to: Optional[str] = None
    rag_query: Optional[str] = None
    threshold: float = 0.6

    @classmethod
    def from_sql_row(cls, row):
        """Create ListFilterDB instance from SQLite row"""
        return cls(
            id=row["id"],
            list_source_id=row["list_source_id"],
            date_range_from=row["date_range_from"],
            date_range_to=row["date_range_to"],
            rag_query=row["rag_query"],
            threshold=row["threshold"],
        )


class DatasourceAuthorDB(BaseModel):
    id: int
    list_source_id: int
    author: str

    @classmethod
    def from_sql_row(cls, row):
        """Create DatasourceAuthorDB instance from SQLite row"""
        return cls(
            id=row["id"], list_source_id=row["list_source_id"], author=row["author"]
        )


# API models (for backwards compatibility and API responses)
class SmartListFilter(BaseModel):
    dateRange: Dict[str, str]
    ragQuery: str
    threshold: float
    authors: List[str] = []


class ListSource(BaseModel):
    dataSourceId: str
    filters: SmartListFilter


# class SmartList(BaseModel):
#     id: int
#     name: str
#     listSources: List[ListSource]
#     computedItems: List = []
#     itemCount: int


# Connected API result model
class SmartListAPIResult(BaseModel):
    id: int
    name: str
    listSources: List[ListSource]
    computedItems: List = []
    itemCount: int
    owner_email: str
    following: bool = False

    @classmethod
    def from_db_data(
        cls, smart_list: SmartListDB, sources_data: List[Dict], following: bool = False
    ):
        """Create SmartListAPIResult from database data"""
        # Group sources by list_source_id
        sources_by_id = {}
        for row in sources_data:
            source_id = row["source_id"]
            if source_id not in sources_by_id:
                sources_by_id[source_id] = {
                    "dataSourceId": row["data_source_id"],
                    "filters": {
                        "dateRange": {
                            "from": row["date_range_from"],
                            "to": row["date_range_to"],
                        },
                        "ragQuery": row["rag_query"] or "",
                        "threshold": row["threshold"] or 0.6,
                        "authors": [],
                    },
                }

            # Add author if present
            if row["author"]:
                sources_by_id[source_id]["filters"]["authors"].append(row["author"])

        # Convert to ListSource models
        list_sources = []
        for source_data in sources_by_id.values():
            filters = SmartListFilter(**source_data["filters"])
            list_source = ListSource(
                dataSourceId=source_data["dataSourceId"], filters=filters
            )
            list_sources.append(list_source)

        return cls(
            id=smart_list.id,
            name=smart_list.name,
            listSources=list_sources,
            itemCount=smart_list.item_count,
            owner_email=smart_list.user_email,
            following=following,
        )


class SmartListCreate(BaseModel):
    name: str
    listSources: List[ListSource]


class TweetItem(BaseModel):
    id: Union[
        str, int
    ]  # Allow both string (for real tweet IDs) and int (for mock data)
    type: str
    content: str
    author: Dict
    likes: int
    reactions: int
    timestamp: str
    similarity_score: Optional[float] = None
    tweet_type: str = "original"  # "original", "repost", "quote", "reply"
    interaction_context: Dict = {}
    media: Optional[str] = None  # JSON string containing media data


class Message(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str


class Chat(BaseModel):
    id: int
    messages: List[Message]


class QuestionRequest(BaseModel):
    question: str
    context: list[str]

    def format_for_anthropic(self):
        return f"Question: {self.question}\nContext: {self.context}"


class SummaryResponse(BaseModel):
    summary: str
    status: str
    model: Optional[str] = None


class UserCreate(BaseModel):
    email: str


class User(BaseModel):
    id: int
    email: str
    created_at: str

    @classmethod
    def from_sql_row(cls, row):
        """Create User instance from SQLite row"""
        return cls(id=row[0], email=row[1], created_at=row[2])
