from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = False
    skip_auth: bool = False
    syftbox_email: str = ""
    syftbox_access_token: str = ""
    syftbox_queryengine_port: int = 8002
    dev_email: str = "dev@openmined.org"
    dev_access_token: str = "dev_mode"


settings = Settings()
