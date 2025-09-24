from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from omni.db import (
    create_user,
    follow_list,
    get_followed_list_ids,
    get_omni_connection,
    get_user_by_email,
    initialize_dev_user,
    unfollow_list,
)
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
    User,
    UserCreate,
)
from omni.settings import settings
from omni.summaries import clear_summary_cache as clear_cache
from omni.summaries import (
    generate_filters_hash,
    get_anthropic_completion,
    get_or_generate_smart_list_summary,
)
from omni.twitter import query_twitter_data

app = FastAPI(title="Omni API", description="Backend API for Omni application")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:8005"],  # Vite dev server
    allow_origins=["*"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and dev user on startup"""
    try:
        # Initialize the dev user for development
        initialize_dev_user()
        print("✅ Dev user initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize dev user: {e}")


# Routes
@app.get("/")
async def root():
    return {"message": "Omni API is running"}


@app.post("/users/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user or return existing user"""
    with get_omni_connection() as conn:
        user_row = create_user(conn, user_data.email)
        if user_row:
            return User.from_sql_row(user_row)
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")


@app.get("/users/{email}", response_model=User)
async def get_user(email: str):
    """Get user by email"""
    with get_omni_connection() as conn:
        user_row = get_user_by_email(conn, email)
        if user_row:
            return User.from_sql_row(user_row)
        else:
            raise HTTPException(status_code=404, detail="User not found")


@app.get("/data-sources", response_model=List[DataSource])
async def get_data_sources():
    return get_mock_data_sources()


@app.get("/data-collections", response_model=List[DataCollection])
async def get_data_collections():
    return get_mock_data_collections()


@app.get("/smart-lists", response_model=List[SmartList])
async def get_all_smart_lists():
    """Get all available smart lists"""
    return get_mock_smart_lists()


@app.get("/smart-lists/followed", response_model=List[SmartList])
async def get_followed_smart_lists(user_email: str = "dev@example.com"):
    """Get smart lists that the user is following"""
    with get_omni_connection() as conn:
        followed_list_ids = get_followed_list_ids(conn, user_email)

    all_lists = get_mock_smart_lists()
    followed_lists = [
        list_item for list_item in all_lists if list_item["id"] in followed_list_ids
    ]

    return followed_lists


@app.post("/smart-lists/{list_id}/follow")
async def follow_smart_list(list_id: int, user_email: str = "dev@example.com"):
    """Follow a smart list"""
    with get_omni_connection() as conn:
        follow_list(conn, user_email, list_id)
    return {"message": f"Successfully followed list {list_id}"}


@app.delete("/smart-lists/{list_id}/follow")
async def unfollow_smart_list(list_id: int, user_email: str = "dev@example.com"):
    """Unfollow a smart list"""
    with get_omni_connection() as conn:
        unfollow_list(conn, user_email, list_id)
    return {"message": f"Successfully unfollowed list {list_id}"}


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
