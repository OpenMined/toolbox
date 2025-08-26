def get_default_notification_topic() -> str:
    import hashlib
    import os

    from toolbox.analytics import get_anonymous_user_id

    username = (
        os.getenv("USER")
        or os.getenv("USERNAME")
        or os.path.basename(os.path.expanduser("~"))
    )

    # Add 4 chars from analytics ID for uniqueness
    user_id = get_anonymous_user_id()
    short_hash = hashlib.sha256(user_id.encode()).hexdigest()[:4]

    return f"tb-{username}-{short_hash}"  # e.g., tb-eelco-a3f2
