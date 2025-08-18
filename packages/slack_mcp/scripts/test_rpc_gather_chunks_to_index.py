from slack_mcp.settings import settings
from slack_mcp.syftbox_client import create_authenticated_client

settings.dev_mode = True
client = create_authenticated_client(
    app_name="slack-mcp",
    user_email=settings.syftbox_email,
    access_token=settings.syftbox_access_token,
)


payload = [10]
response = client.post("/get_new_chunks", json=payload)
print(response.json())
