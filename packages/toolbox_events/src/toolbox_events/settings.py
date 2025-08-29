from pydantic_settings import BaseSettings, SettingsConfigDict


class EventSinkSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TOOLBOX_EVENTS_SINK_",
        case_sensitive=False,
    )

    kind: str = "memory"
    source_name: str = "unknown"

    # HTTP sink settings
    daemon_url: str = "http://localhost:8000"
    timeout: float = 30.0
    headers: dict[str, str] = {}


class EventSourceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TOOLBOX_EVENTS_SOURCE_",
        case_sensitive=False,
    )

    kind: str = "stdin"
