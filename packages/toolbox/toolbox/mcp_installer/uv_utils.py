import subprocess
import sys
from pathlib import Path

POSSIBLE_UV_PATHS = [
    "/usr/local/bin/uv",  # Intel Macs (x86)
    "/opt/homebrew/bin/uv",  # Apple Silicon (M1/M2/M3)
    "/usr/local/bin/uv",
    "~/.local/bin/uv",
    "~/.cargo/bin/uv",
    "/usr/bin/uv",
    "/opt/uv/uv",
    "~/bin/uv",
]


def init_venv_uv(installation_dir: Path):
    _ = subprocess.run(
        ["uv", "venv", "--python", "3.12"],
        cwd=installation_dir,
        check=True,
        capture_output=True,
    )


def set_uv_path_in_env(env: dict):
    uv_path = find_uv_path()
    if uv_path is not None:
        current_PATH = env.get("PATH", "")
        if str(uv_path) not in current_PATH:
            env["PATH"] = f"{uv_path}:{current_PATH}"
    return env


def check_uv_installed():
    try:
        _ = subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv is not installed. Please install uv first.")
        sys.exit(1)


def find_uv_path():
    result = subprocess.run(["which", "uv"], capture_output=True, text=True)
    uv_path = result.stdout.strip()
    if "/" in uv_path:
        return Path(uv_path).expanduser()
    else:
        for path_str in POSSIBLE_UV_PATHS:
            path = Path(path_str)
            if path.exists():
                return path.expanduser()
        return None
