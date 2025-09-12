import uuid
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


def _get_anonymous_id_file():
    """Get the analytics ID file path"""
    from toolbox.settings import TOOLBOX_SETTINGS_DIR

    config_dir = TOOLBOX_SETTINGS_DIR
    config_dir.mkdir(exist_ok=True)
    return config_dir / ".analytics_id"


def set_anonymous_user_id(user_id: str) -> None:
    """Set the anonymous user ID"""
    id_file = _get_anonymous_id_file()
    id_file.write_text(user_id)


def get_anonymous_user_id() -> str:
    """Generate stable anonymous ID using config directory"""
    id_file = _get_anonymous_id_file()

    if id_file.exists():
        return id_file.read_text().strip()

    # Generate new ID
    new_id = str(uuid.uuid4())
    set_anonymous_user_id(new_id)
    return new_id


def get_default_notification_topic() -> str:
    """
    Get a unique default topic for this user: "tb-<username>-<user_id[:4]>"

    Returns:
        str: The default notification topic
    """
    username = Path.home().name

    # Add 4 chars from user ID for uniqueness
    user_id = get_anonymous_user_id()

    return f"tb-{username}-{user_id[:4]}"


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

    # Notification settings
    default_notification_topic: str = Field(
        default_factory=get_default_notification_topic
    )

    model_config = SettingsConfigDict(
        json_file=TOOLBOX_CONFIG_FILE,
        nested_model_default_partial_update=True,
        env_prefix="TOOLBOX_",
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
