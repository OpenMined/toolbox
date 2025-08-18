from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    embedding_provider: str = "ollama"  # "ollama" or "syftbox"
    max_messages_per_hour: int = 100
    ollama_port: int = 11434
    discord_mcp_port: int = 8005

    @property
    def ollama_url(self) -> str:
        return f"http://localhost:{self.ollama_port}"


settings = Settings()
