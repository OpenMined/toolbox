from pathlib import Path

HOME = Path.home()


def installation_dir_from_name(name: str):
    return HOME / ".toolbox" / "installed" / name
