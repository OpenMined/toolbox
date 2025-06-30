import json
from pathlib import Path
import requests

HOME_DIR = Path.home()
DEFAULT_SCREENPIPE_DB_DIR = HOME_DIR / ".screenpipe"
DEFAULT_SYFTBOX_CONFIG_PATH = HOME_DIR / ".syftbox" / "config.json"


def screenpipe_installed(screenpipe_db_dir: Path | str = DEFAULT_SCREENPIPE_DB_DIR):
    screenpipe_db_dir = Path(screenpipe_db_dir)
    screenpipe_db_path = screenpipe_db_dir / "db.sqlite"
    return screenpipe_db_path.exists()


def syftbox_installed(syftbox_config_path: Path | str = DEFAULT_SYFTBOX_CONFIG_PATH):
    syftbox_config_path = Path(syftbox_config_path)
    return syftbox_config_path.exists()


def syftbox_running(syftbox_port: int = 7938):
    try:
        response = requests.get(f"http://localhost:{syftbox_port}/")
    except Exception:
        return False
    return response.status_code == 200


def get_syftbox_email(syftbox_config_path: Path | str = DEFAULT_SYFTBOX_CONFIG_PATH):
    with open(syftbox_config_path, "r") as f:
        config = json.load(f)
    return config["email"]
