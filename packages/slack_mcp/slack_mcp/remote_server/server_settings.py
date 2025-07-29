from pydantic import BaseModel


class ServerSettings(BaseModel):
    # "http://4.151.234.109:8020 in prod"
    nomic_url: str = "http://localhost"
    nomic_port: int = 8020
    nomic_secret_key: str = ""
    use_mock_embeddings: bool = True


settings = ServerSettings()
