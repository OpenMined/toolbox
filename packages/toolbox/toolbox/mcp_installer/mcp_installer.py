import re
import subprocess
import sys
from pathlib import Path

import psutil
import os

from toolbox.utils.utils import DEFAULT_LOG_FILE, installation_dir_from_name

HOME = Path.home()


def check_uv_installed():
    try:
        _ = subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv is not installed. Please install uv first.")
        sys.exit(1)


def make_mcp_installation_dir(name: str):
    installation_dir = installation_dir_from_name(name)
    installation_dir.mkdir(parents=True, exist_ok=True)
    return installation_dir


def init_venv_uv(installation_dir: Path):
    _ = subprocess.run(
        ["uv", "venv", "--python", "3.12"],
        cwd=installation_dir,
        check=True,
        capture_output=True,
    )


def install_package_from_local_path(installation_dir: Path, package_path: Path):
    # print(f"Installing package from local path: {package_path}")
    try:
        cmd = f"source .venv/bin/activate && uv pip install -q -e {package_path}"
        result = subprocess.run(
            cmd,
            cwd=installation_dir,
            executable="/bin/bash",
            shell=True,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Failed to install package using running:\n{cmd} in {installation_dir}:\n{e.stderr}\n "
        ) from e

    # print(result.stdout, result.stderr)
    if result.returncode != 0:
        print(f"Failed to install package: {result.stderr}")
        raise Exception(f"Failed to install package: {result.stderr}")


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

    if result.returncode != 0:
        print(f"Failed to install package: {result.stderr}")
        raise Exception(f"Failed to install package: {result.stderr}")


def process_exists(pattern):
    regex = re.compile(pattern)
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if not cmdline or not isinstance(cmdline, list):
                continue  # Skip if cmdline is None or not a list
            cmdline_str = " ".join(cmdline)
            if regex.search(cmdline_str):
                print(f"Process {cmdline_str} exists")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def pkill_f(pattern):
    regex = re.compile(pattern)
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if not cmdline or not isinstance(cmdline, list):
                continue  # Skip if cmdline is None or not a list
            cmdline_str = " ".join(cmdline)
            if regex.search(cmdline_str):
                print(f"Killing PID {proc.pid}: {cmdline_str}")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def should_kill_existing_process(module: str):
    should_kill = input(f"Process {module} already running. Kill it? (y/n)")
    if should_kill in ["y", "Y"]:
        return True
    elif should_kill in ["n", "N"]:
        return False
    else:
        print("Invalid input. Please enter y or n.")
        return should_kill_existing_process(module)


def run_python_mcp(installation_dir: Path, mcp_module: str, env: dict = None):
    SHELL = os.environ.get("SHELL", "/bin/sh")

    cmd = f'{SHELL} -c "source .venv/bin/activate && uv run python -m {mcp_module} > {DEFAULT_LOG_FILE} 2>&1"'
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=installation_dir,
        text=True,
        executable=SHELL,
        env=env,
    )

    # try:
    #     stdout, stderr = proc.communicate(timeout=5)
    #     if proc.returncode != 0:
    #         print(f"Process finished with error within 5 seconds (code {proc.returncode}):")
    #         raise Exception(stderr.decode())
    # except subprocess.TimeoutExpired:
    #     return

    # return stdout.decode()
