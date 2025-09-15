from typing import Dict, List

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
    id: int
    type: str
    content: str
    author: Dict
    likes: int
    reactions: int
    timestamp: str


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
