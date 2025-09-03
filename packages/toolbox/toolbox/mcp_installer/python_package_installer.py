import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext
    from toolbox.store.store_code import StoreElement

from toolbox.mcp_installer.mcp_installer import (
    make_mcp_installation_dir,
    pkill_f,
    process_exists,
    should_kill_existing_process,
)
from toolbox.mcp_installer.uv_utils import (
    check_uv_installed,
    init_venv_uv,
    prepare_env_with_uv,
)
from toolbox.settings import settings
from toolbox.triggers.trigger_utils import add_event_sink_to_env
from toolbox.utils.utils import DEFAULT_LOG_FILE


def uvx_path() -> Path:
    result = subprocess.run(["which", "uvx"], capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError("uvx is not installed")
    return Path(result.stdout.strip()).expanduser()


def run_python_mcp(installation_dir: Path, mcp_module: str, env: dict | None = None):
    SHELL = os.environ.get("SHELL", "/bin/sh")
    final_env = prepare_env_with_uv(env)

    cmd = f'{SHELL} -c "which uv && source .venv/bin/activate && nohup uv run python -m {mcp_module} > {DEFAULT_LOG_FILE} 2>&1 &"'
    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=installation_dir,
        text=True,
        executable=SHELL,
        env=final_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status_code = proc.wait(timeout=15)
    if status_code != 0:
        stdout, stderr = proc.communicate(timeout=5)
        raise Exception(
            f"Could not start MCP process from {installation_dir} (code {status_code}): {stderr.decode()}\n{stdout.decode()}"
        )


def install_python_package_from_local_path(installation_dir: Path, package_path: Path):
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


def install_python_package_from_git(
    installation_dir: Path,
    package_url: str,
    subdirectory: str | None = None,
    branch: str = "main",
):
    subdir_postfix = ""
    if subdirectory:
        subdir_postfix = f"#subdirectory={subdirectory}"
    url = f"git+{package_url}.git@{branch}{subdir_postfix}"
    cmd = f"source .venv/bin/activate && uv pip install -U {url}"
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=installation_dir,
        executable="/bin/bash",  # This is critical
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(
            f"Failed to install package with cmd: {cmd} in {installation_dir}:\n{result.stderr}"
        )


def install_python_mcp(store_element: "StoreElement", context: "InstallationContext"):
    mcp = context.mcp

    check_uv_installed()
    installation_dir = make_mcp_installation_dir(context.current_app)
    init_venv_uv(installation_dir)

    if settings.use_local_packages:
        install_python_package_from_local_path(
            installation_dir,
            store_element.local_package_path,
        )
    else:
        install_python_package_from_git(
            installation_dir,
            package_url=store_element.package_url,
            subdirectory=store_element.subdirectory,
            branch=store_element.branch,
        )

    module = mcp.deployment["module"]
    start_process = True
    if process_exists(module):
        kill_process = should_kill_existing_process(module)
        if kill_process:
            pkill_f(module)
        else:
            start_process = False

    env = context.context_settings
    add_event_sink_to_env(env, mcp.name, settings.daemon.url)

    if start_process:
        run_python_mcp(
            installation_dir,
            module,
            env=env,
        )
