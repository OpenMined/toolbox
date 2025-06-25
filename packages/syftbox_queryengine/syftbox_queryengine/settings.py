from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = Field(default=False)
    skip_auth: bool = Field(default=False)
    syftbox_email: str = Field(default="")
    syftbox_access_token: str = Field(default="")
    syftbox_queryengine_port: int = Field(default=8002)

    dev_email: str = "dev@openmined.org"
    dev_access_token: str = "dev_mode"

settings = Settings()
