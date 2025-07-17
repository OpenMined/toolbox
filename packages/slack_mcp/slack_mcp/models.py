from pydantic import BaseModel


class MatchedContact(BaseModel):
    query: str
    name: str
    score: float
    channel_id: str


class NamesMatchResponse(BaseModel):
    matches_in_favourites: list[MatchedContact]
    matches_in_all: list[MatchedContact]
