from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from omni.mock_data import (
    get_mock_chats,
    get_mock_data_collections,
    get_mock_data_sources,
    get_mock_smart_lists,
    get_mock_summary,
)
from omni.models import (
    Chat,
    DataCollection,
    DataSource,
    QuestionRequest,
    SmartList,
    SmartListCreate,
    SummaryResponse,
    TweetItem,
)
from omni.settings import settings
from omni.twitter import (
    get_anthropic_completion,
    get_or_generate_smart_list_summary,
    query_twitter_data,
)

app = FastAPI(title="Omni API", description="Backend API for Omni application")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8005"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/")
async def root():
    return {"message": "Omni API is running"}


@app.get("/data-sources", response_model=List[DataSource])
async def get_data_sources():
    return get_mock_data_sources()


@app.get("/data-collections", response_model=List[DataCollection])
async def get_data_collections():
    return get_mock_data_collections()


@app.get("/smart-lists", response_model=List[SmartList])
async def get_smart_lists():
    return get_mock_smart_lists()


@app.post("/smart-lists", response_model=SmartList)
async def create_smart_list(list_data: SmartListCreate):
    new_list = {
        "id": int(str(int(1000000000000))[:10]),  # Generate timestamp-based ID
        "name": list_data.name,
        "listSources": [source.dict() for source in list_data.listSources],
        "computedItems": [],
        "itemCount": 0,
    }
    return new_list


@app.get("/smart-lists/{list_id}/items", response_model=List[TweetItem])
async def get_smart_list_items(list_id: int):
    # Get smart list configuration
    smart_lists = get_mock_smart_lists()
    smart_list = next((sl for sl in smart_lists if sl["id"] == list_id), None)

    if not smart_list:
        raise HTTPException(status_code=404, detail="Smart list not found")

    # Check if this list has Twitter sources with real data
    for list_source in smart_list["listSources"]:
        if list_source["dataSourceId"] == "twitter":
            # Use real Twitter data
            items = query_twitter_data(list_source)
            return items

    # Fallback to mock data
    # items = get_mock_smart_list_items(list_id)
    if not items:
        raise HTTPException(status_code=404, detail="Smart list not found")
    return items


@app.get("/smart-lists/{list_id}/summary", response_model=SummaryResponse)
async def get_smart_list_summary(list_id: int):
    # Get smart list configuration
    smart_lists = get_mock_smart_lists()
    smart_list = next((sl for sl in smart_lists if sl["id"] == list_id), None)

    if not smart_list:
        raise HTTPException(status_code=404, detail="Smart list not found")

    # Check if this list has Twitter sources for dynamic summary
    for list_source in smart_list["listSources"]:
        if list_source["dataSourceId"] == "twitter" and list_source["filters"].get(
            "authors"
        ):
            # Get cached or generate dynamic summary from tweets
            result = get_or_generate_smart_list_summary(list_id, list_source)
            return result

    # Fallback to mock summary
    summary = get_mock_summary(list_id)
    if not summary:
        return {
            "summary": "No summary available for this list.",
            "status": "error",
            "model": None,
        }
    return {"summary": summary, "status": "completed", "model": None}


@app.delete("/smart-lists/{list_id}/summary/cache")
async def clear_summary_cache(list_id: int):
    """Clear cached summary for testing purposes"""
    from omni.mock_data import get_mock_smart_lists
    from omni.twitter import generate_filters_hash
    from omni.vectorstore_queries import clear_summary_cache as clear_cache

    smart_lists = get_mock_smart_lists()
    smart_list = next((sl for sl in smart_lists if sl["id"] == list_id), None)

    if not smart_list:
        raise HTTPException(status_code=404, detail="Smart list not found")

    for list_source in smart_list["listSources"]:
        if list_source["dataSourceId"] == "twitter":
            filters_hash = generate_filters_hash(list_source)
            return clear_cache(list_id, filters_hash)

    return {"message": "No Twitter sources found for this list"}


@app.get("/chats/{list_id}", response_model=List[Chat])
async def get_chats(list_id: int):
    chats = get_mock_chats(list_id)
    return chats


@app.post("/chats/{list_id}/ask")
async def ask_question(list_id: int, request: QuestionRequest):
    # Mock response for asking questions
    if settings.use_anthropic:
        response = get_anthropic_completion(request.format_for_anthropic())
        return {
            "id": 999,
            "role": "assistant",
            "answer": response,
            "timestamp": "2024-01-15T10:00:00Z",
        }
    else:
        response = {
            "id": 999,
            "role": "assistant",
            "answer": f"This is a mock response to your question: '{request.question}' about list {list_id}",
            "timestamp": "2024-01-15T10:00:00Z",
        }
        return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
