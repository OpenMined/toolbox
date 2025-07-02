from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dev_mode: bool = Field(default=False)
    create_dev_user: bool = Field(default=False)
    use_mock_transcription: bool = Field(default=True)
    deepgram_api_key: str = Field(default="")
    whisper_url: str = Field(default="4.151.234.109:8006")
    whisper_secret_key: str = Field(default="")

    class Config:
        env_file = ".env"


settings = Settings()
