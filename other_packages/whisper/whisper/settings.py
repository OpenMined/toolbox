from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    whisper_secret_key: str = "dev_key"


settings = Settings()
