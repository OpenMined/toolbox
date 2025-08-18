from typing import Optional

from fastapi import Header

from slack_mcp.settings import settings


def get_syftbox_credentials():
    syftbox_email = settings.syftbox_email
    syftbox_access_token = settings.syftbox_access_token
    if settings.skip_auth:
        return settings.dev_email, settings.dev_access_token

    if syftbox_email is None and settings.dev_mode:
        syftbox_email = settings.dev_email
        syftbox_access_token = settings.dev_access_token

    if syftbox_email is None:
        raise ValueError("SYFTBOX_EMAIL is not set")

    return syftbox_email, syftbox_access_token


def authenticate(x_access_token: Optional[str] = Header(None)):
    print("settings.skip_auth", settings.skip_auth)
    if x_access_token is None and not (settings.dev_mode or settings.skip_auth):
        raise ValueError("X-Access-Token is not for authentication")

    if settings.skip_auth:
        return "dev@openmined.org"

    email, syftbox_access_token = get_syftbox_credentials()
    if x_access_token[:5] != syftbox_access_token[:5]:
        raise ValueError(
            f"Invalid credentials. Queryengine:{syftbox_access_token[:5]} != passed:{x_access_token[:5]}"
        )
    return email
