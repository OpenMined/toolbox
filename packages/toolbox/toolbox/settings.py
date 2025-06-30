from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_local_packages: bool = Field(default=False)
    use_local_deployments: bool = Field(default=False)
    request_syftbox_login: bool = Field(default=False)


settings = Settings()
