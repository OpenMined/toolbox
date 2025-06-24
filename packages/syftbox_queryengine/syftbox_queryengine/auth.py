import os
from typing import Optional

from fastapi import Header

from syftbox_queryengine.settings import settings

SYFTBOX_EMAIL_KEY = "SYFTBOX_EMAIL"
SYFTBOX_ACCESS_TOKEN_KEY = "SYFTBOX_ACCESS_TOKEN"

DEV_EMAIL = "dev@openmined.org"
DEV_ACCESS_TOKEN = "dev_mode"


def get_syftbox_credentials():
    syftbox_email = os.environ.get(SYFTBOX_EMAIL_KEY)
    if settings.skip_auth:
        return DEV_EMAIL, DEV_ACCESS_TOKEN

    if syftbox_email is None and settings.dev_mode:
        syftbox_email = DEV_EMAIL
        syftbox_access_token = os.environ.get(
            SYFTBOX_ACCESS_TOKEN_KEY, DEV_ACCESS_TOKEN
        )

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
        print("Invalid credentials", x_access_token[:5], syftbox_access_token[:5])
        raise ValueError("Invalid credentials")
    return email
