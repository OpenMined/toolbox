import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"
