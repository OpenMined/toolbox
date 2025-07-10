import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_local_packages: bool = Field(default=False)
    use_local_deployments: bool = Field(default=False)
    request_syftbox_login: bool = Field(default=False)
    working_directory: Path = Field(default_factory=lambda: Path(os.getcwd()))


settings = Settings()
