from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = False
    skip_auth: bool = False
    syftbox_email: str = ""
    syftbox_access_token: str = ""
    start_polling_thread: bool = True
    slack_mcp_port: int = 8004
    dev_email: str = "dev@openmined.org"
    dev_access_token: str = "dev_mode"


settings = Settings()
