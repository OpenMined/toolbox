from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

TOOLBOX_DIR = Path(__file__).parent.parent
TOOLBOX_WORKSPACE_DIR = TOOLBOX_DIR.parent.parent


class Settings(BaseSettings):
    use_local_packages: bool = Field(default=False)
    use_local_deployments: bool = Field(default=False)
    request_syftbox_login: bool = Field(default=False)
    skip_slack_auth: bool = Field(default=False)
    verbose: int = Field(default=0)
    do_whatsapp_desktop_check: bool = Field(default=True)


settings = Settings()
