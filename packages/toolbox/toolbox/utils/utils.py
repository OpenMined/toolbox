from pathlib import Path

HOME = Path.home()


DEFAULT_LOG_FILE = "mcp_logs.txt"


def installation_dir_from_name(name: str):
    return HOME / ".toolbox" / "installed" / name
