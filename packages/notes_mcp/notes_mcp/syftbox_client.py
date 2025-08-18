from typing import Optional

from fastsyftbox.simple_client import SimpleRPCClient

from notes_mcp.settings import settings


def create_authenticated_client(
    app_name: str = "data-syncer",
    user_email: Optional[str] = None,
    access_token: Optional[str] = None,
) -> SimpleRPCClient:
    """Create a SimpleRPCClient with authentication headers."""
    headers = {"X-User-Email": user_email, "X-Access-Token": access_token}
    if settings.dev_mode:
        return SimpleRPCClient.for_local_transport(app_name=app_name, headers=headers)
    else:
        return SimpleRPCClient.for_syftbox_transport(
            app_owner=user_email, app_name=app_name, headers=headers
        )
