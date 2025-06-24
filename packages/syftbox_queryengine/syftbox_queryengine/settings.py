from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = Field(default=False)
    skip_auth: bool = Field(default=False)


settings = Settings()
