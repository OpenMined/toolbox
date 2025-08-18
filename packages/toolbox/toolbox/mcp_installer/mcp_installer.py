import re
from pathlib import Path

import psutil

from toolbox.utils.utils import installation_dir_from_name

HOME = Path.home()


def make_mcp_installation_dir(name: str):
    installation_dir = installation_dir_from_name(name)
    installation_dir.mkdir(parents=True, exist_ok=True)
    return installation_dir


def process_exists(pattern):
    regex = re.compile(pattern)
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline")
            if not cmdline or not isinstance(cmdline, list):
                continue  # Skip if cmdline is None or not a list
            cmdline_str = " ".join(cmdline)
            if regex.search(cmdline_str):
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
