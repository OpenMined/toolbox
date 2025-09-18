from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_anthropic: bool = False


settings = Settings()
