from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    obsidian_mcp_port: int = 8007
    obsidian_vault_path: Path | None = None


settings = Settings()
