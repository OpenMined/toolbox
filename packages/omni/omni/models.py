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


class SmartListFilter(BaseModel):
    dateRange: Dict[str, str]
    ragQuery: str
    threshold: float
    authors: List[str] = []


class ListSource(BaseModel):
    dataSourceId: str
    filters: SmartListFilter


class SmartList(BaseModel):
    id: int
    name: str
    listSources: List[ListSource]
    computedItems: List = []
    itemCount: int


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
