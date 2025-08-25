from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

TOOLBOX_DIR = Path(__file__).parent.parent
TOOLBOX_WORKSPACE_DIR = TOOLBOX_DIR.parent.parent
TOOLBOX_SETTINGS_DIR = Path.home() / ".toolbox"
TOOLBOX_CONFIG_FILE = TOOLBOX_SETTINGS_DIR / "config.json"


class DaemonSettings(BaseModel):
    db_path: Path = TOOLBOX_SETTINGS_DIR / "daemon.db"
    log_file: Path | None = TOOLBOX_SETTINGS_DIR / "daemon.log"
    pid_file: Path = TOOLBOX_SETTINGS_DIR / "daemon.pid"
    enable_scheduler: bool = True
    max_concurrent_triggers: int = Field(default=4)
    host: str = "127.0.0.1"
    port: int = 8111

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path.as_posix()}"

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class Settings(BaseSettings):
    use_local_packages: bool = Field(default=False)
    use_local_deployments: bool = Field(default=False)
    request_syftbox_login: bool = Field(default=False)
    analytics_enabled: bool = Field(default=True)
    dev_mode: bool = Field(default=False)
    verbose: int = Field(default=0)
    daemon: DaemonSettings = Field(default_factory=DaemonSettings)

    # MCP-specific settings
    skip_slack_auth: bool = Field(default=False)
    do_whatsapp_desktop_check: bool = Field(default=True)
    use_discord_env_var: bool = Field(default=True)

    model_config = SettingsConfigDict(
        json_file=TOOLBOX_CONFIG_FILE,
        nested_model_default_partial_update=True,
    )

    @property
    def first_time_setup(self):
        return not TOOLBOX_CONFIG_FILE.exists()

    @property
    def settings_path(self):
        return TOOLBOX_CONFIG_FILE

    def save(self):
        TOOLBOX_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        TOOLBOX_CONFIG_FILE.write_text(self.model_dump_json(indent=2))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # settings order: json -> env file -> env -> defaults
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            JsonConfigSettingsSource(settings_cls),
        )


settings = Settings()
