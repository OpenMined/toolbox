from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mock_data import (
    get_mock_chats,
    get_mock_data_collections,
    get_mock_data_sources,
    get_mock_smart_list_items,
    get_mock_smart_lists,
    get_mock_summary,
)
from models import (
    Chat,
    DataCollection,
    DataSource,
    QuestionRequest,
    SmartList,
    SmartListCreate,
    TweetItem,
)

app = FastAPI(title="Omni API", description="Backend API for Omni application")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
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
    items = get_mock_smart_list_items(list_id)
    if not items:
        raise HTTPException(status_code=404, detail="Smart list not found")
    return items


@app.get("/smart-lists/{list_id}/summary")
async def get_smart_list_summary(list_id: int):
    summary = get_mock_summary(list_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Smart list not found")
    return {"summary": summary}


@app.get("/chats/{list_id}", response_model=List[Chat])
async def get_chats(list_id: int):
    chats = get_mock_chats(list_id)
    return chats


@app.post("/chats/{list_id}/ask")
async def ask_question(list_id: int, request: QuestionRequest):
    # Mock response for asking questions
    response = {
        "id": 999,
        "role": "assistant",
        "content": f"This is a mock response to your question: '{request.question}' about list {list_id}",
        "timestamp": "2024-01-15T10:00:00Z",
    }
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
