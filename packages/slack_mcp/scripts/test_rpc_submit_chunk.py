import uuid

from slack_mcp.models import Chunk
from slack_mcp.settings import settings
from slack_mcp.syftbox_client import create_authenticated_client

settings.dev_mode = True
client = create_authenticated_client(
    app_name="slack-mcp",
    user_email=settings.syftbox_email,
    access_token=settings.syftbox_access_token,
)


payload = [
    Chunk(
        chunk_id=str(uuid.uuid4()),
        channel_ids=["C0123456789"],
        tss=["1234567890.123456"],
        chunk_text="Hello, world!",
        embedding=[0.1] * 768,
    ).model_dump(mode="json")
]
response = client.post("/submit_chunks", json=payload)
print(response.json())
