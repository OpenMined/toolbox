from pathlib import Path

from pydantic import Field
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


class Settings(BaseSettings):
    use_local_packages: bool = Field(default=False)
    use_local_deployments: bool = Field(default=False)
    request_syftbox_login: bool = Field(default=False)
    skip_slack_auth: bool = Field(default=False)
    verbose: int = Field(default=0)
    do_whatsapp_desktop_check: bool = Field(default=True)

    analytics_enabled: bool = Field(default=True)

    model_config = SettingsConfigDict(json_file=TOOLBOX_CONFIG_FILE)

    @property
    def first_time_setup(self):
        return not TOOLBOX_CONFIG_FILE.exists()

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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            JsonConfigSettingsSource(settings_cls),
        )


settings = Settings()
