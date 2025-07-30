from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    # "http://4.151.234.109:8020 in prod"
    nomic_url: str = "http://localhost"
    nomic_port: int = 8020
    server_port: int = 8005
    nomic_secret_key: str = ""
    use_mock_embeddings: bool = True
    create_dev_user: bool = False
    dev_mode: bool = False


settings = ServerSettings()
