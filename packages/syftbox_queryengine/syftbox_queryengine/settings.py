from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = Field(default=True)


settings = Settings()
