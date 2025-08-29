import os
import traceback
from functools import wraps
from typing import Any, Dict, Optional

from posthog import Posthog, identify_context

from toolbox import __version__
from toolbox.settings import get_anonymous_user_id, settings

# PostHog configuration
# safe to hardcode, its a public write-only key
POSTHOG_PUBLIC_KEY = os.getenv(
    "POSTHOG_API_KEY", default="phc_TropYqZrmdCFGIawoLCB7auDIfBMwjTNJlJbd4EJuQg"
)
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

posthog = Posthog(
    project_api_key=POSTHOG_PUBLIC_KEY,
    host=POSTHOG_HOST,
)


if not settings.analytics_enabled:
    posthog.disabled = True


def posthog_safe_capture(
    event_name: str,
    properties: Optional[Dict[str, Any]] = None,
    distinct_id: Optional[str] = None,
    flush: bool = False,
) -> None:
    properties = properties or {}
    properties["toolbox_version"] = __version__
    properties["toolbox_test_user"] = settings.dev_mode

    try:
        user_id = distinct_id or get_anonymous_user_id()
        posthog.capture(
            event_name,
            properties=properties,
            distinct_id=user_id,
        )
        if flush:
            posthog.flush()
    except Exception:
        pass


def track_cli_command(command_name: str = None):
    """Decorator to track command execution with structured arguments and error handling"""

    def _track(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If analytics are disabled, this is a no-op
            if not settings.analytics_enabled:
                return func(*args, **kwargs)

            # Get stable user ID and identify the user in this context
            user_id = get_anonymous_user_id()
            identify_context(user_id)

            cmd_name = command_name or func.__name__
            safe_kwargs = {
                k: v
                for k, v in kwargs.items()
                if not k.startswith("_")
                and "password" not in k.lower()
                and "token" not in k.lower()
            }

            try:
                result = func(*args, **kwargs)

                # Track successful completion
                posthog_safe_capture(
                    "cli command",
                    properties={
                        "command": cmd_name,
                        **safe_kwargs,
                    },
                    flush=True,
                )
                return result

            except Exception as e:
                # log error to posthog and re-raise
                posthog_safe_capture(
                    "cli error",
                    properties={
                        "command": cmd_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e),  # Truncate long errors
                        "traceback": traceback.format_exc(),
                        **safe_kwargs,
                    },
                    flush=True,
                )
                raise

        return wrapper

    return _track
