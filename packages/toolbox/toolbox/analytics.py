import os
import platform
import uuid
from functools import wraps
from typing import Any, Dict, Optional

from posthog import Posthog, identify_context, scoped

from toolbox.settings import TOOLBOX_SETTINGS_DIR, settings


def get_user_id() -> str:
    """Generate stable anonymous ID using config directory"""
    config_dir = TOOLBOX_SETTINGS_DIR
    config_dir.mkdir(exist_ok=True)

    id_file = config_dir / ".analytics_id"

    if id_file.exists():
        return id_file.read_text().strip()

    # Generate new anonymous ID
    new_id = str(uuid.uuid4())
    id_file.write_text(new_id)
    return new_id


# PostHog configuration
PROJECT_API_KEY = os.getenv("POSTHOG_API_KEY")
if not PROJECT_API_KEY:
    # Fallback for development - in production this should be required
    PROJECT_API_KEY = "phc_TropYqZrmdCFGIawoLCB7auDIfBMwjTNJlJbd4EJuQg"

HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

posthog = Posthog(
    project_api_key=PROJECT_API_KEY,
    host=HOST,
    debug=os.getenv("TOOLBOX_DEBUG", "false").lower() == "true",
)

# Disable in test environments
if os.getenv("TOOLBOX_ENVIRONMENT") == "test" or not settings.analytics_enabled:
    posthog.disabled = True


def safe_capture(
    event_name: str,
    properties: Optional[Dict[str, Any]] = None,
    distinct_id: Optional[str] = None,
) -> None:
    try:
        # Use provided distinct_id, our persistent user ID, or let PostHog handle anonymous tracking
        user_id = distinct_id or get_user_id()
        posthog.capture(
            event_name,
            properties={
                **(properties or {}),
                "os": platform.system(),
                "python_version": platform.python_version(),
                "$process_person_profile": False,
            },
            distinct_id=user_id,
        )
    except Exception:
        if os.getenv("TOOLBOX_DEBUG", "false").lower() == "true":
            import traceback

            traceback.print_exc()


def track_cli_command(command_name: str, args: dict = None):
    """Track when a CLI command is invoked"""
    if command_name:
        properties = {
            "command": command_name,
            "$process_person_profile": False,
        }

        # Add command arguments if provided
        if args:
            properties.update(args)

        safe_capture("cli_command", properties)


def cli_analytics(command_name: str = None):
    """Decorator to track command execution with structured arguments and error handling"""

    def decorator(func):
        @wraps(func)
        @scoped(fresh=True, capture_exceptions=True)
        def wrapper(*args, **kwargs):
            # If analytics are disabled, this is a no-op
            if not settings.analytics_enabled:
                return func(*args, **kwargs)

            # Get stable user ID and identify the user in this context
            user_id = get_user_id()
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
                safe_capture(
                    "cli command_completed",
                    properties={
                        "command": cmd_name,
                        **safe_kwargs,
                    },
                )
                posthog.flush()
                return result

            except Exception as e:
                # Track error
                safe_capture(
                    "cli command_error",
                    properties={
                        "command": cmd_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)[-1000:],  # Truncate long errors
                        **safe_kwargs,
                    },
                )
                posthog.flush()
                raise

        return wrapper

    return decorator
