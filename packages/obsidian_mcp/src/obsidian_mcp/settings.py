from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    obsidian_mcp_port: int = 8007


settings = Settings()
