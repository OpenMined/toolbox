from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_anthropic: bool = False
    use_mock_summaries: bool = False

    x_download_schedule_seconds: int | tuple[int, int] | None = [
        7200 * 2,
        14400 * 2,
    ]  # every 4-8 hours
    use_cached_x_cookies: bool = True


settings = Settings()
