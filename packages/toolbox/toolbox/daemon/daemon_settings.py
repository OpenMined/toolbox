"""Daemon configuration settings"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from toolbox.db import TOOLBOX_DB_DIR


class DaemonSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TOOLBOX_DAEMON_",
        case_sensitive=False,
    )

    db_url: str = f"sqlite:///{TOOLBOX_DB_DIR / 'triggers.db'}"
    enable_scheduler: bool = True
    log_file: Path | None = None
