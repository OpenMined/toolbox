import subprocess
import sys
from pathlib import Path

HOME = Path.home()


def check_uv_installed():
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv is not installed. Please install uv first.")
        sys.exit(1)


def make_mcp_installation_dir(name: str):
    installation_dir = HOME / ".toolbox" / "installations" / name
    installation_dir.mkdir(parents=True, exist_ok=True)
    return installation_dir


def init_venv_uv(installation_dir: Path):
    subprocess.run(
        ["uv", "venv", "--python", "3.12"],
        cwd=installation_dir,
        check=True,
    )


def install_package_from_git(
    installation_dir: Path,
    package_url: str,
    subdirectory: str | None = None,
    branch: str = "main",
):
    subdir_postfix = ""
    if subdirectory:
        subdir_postfix = f"#subdirectory={subdirectory}"
    url = f"git+{package_url}.git@{branch}{subdir_postfix}"
    result = subprocess.run(
        f"source .venv/bin/activate && uv pip install -U {url}",
        shell=True,
        cwd=installation_dir,
        executable="/bin/bash",  # This is critical
        capture_output=True,
        text=True,
    )
    # result = subprocess.run(
    #     "source .venv/bin/activate",
    #     # ["source", ".venv/bin/activate", "&&", "uv", "pip", "install", "-U", url],
    #     shell=True,
    #     cwd=installation_dir,
    #     capture_output=True,
    #     text=True,
    # )

    if result.returncode != 0:
        print(f"Failed to install package: {result.stderr}")
        raise Exception(f"Failed to install package: {result.stderr}")
    print("ABCs")


def run_python_mcp(installation_dir: Path, mcp_module: str):
    subprocess.Popen(
        f"source .venv/bin/activate && uv run python -m {mcp_module}",
        shell=True,
        cwd=installation_dir,
        text=True,
        executable="/bin/bash",
    )
