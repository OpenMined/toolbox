from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_anthropic: bool = False

    x_download_schedule_seconds: int | tuple[int, int] | None = [
        7200,
        14400,
    ]  # every 2-4 hours
    use_cached_x_cookies: bool = True


settings = Settings()
