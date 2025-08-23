import os
import signal
import sys
import time
from pathlib import Path

import uvicorn
from loguru import logger

from toolbox.daemon.app import create_app

SHUTDOWN_WAIT_TIME = 10  # Maximum time to wait for graceful shutdown in seconds


def get_daemon_pid_file() -> Path:
    """Get the path to the daemon PID file"""
    pid_file = Path.home() / ".toolbox" / "daemon.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    return pid_file


def write_pid_file(pid_file: Path) -> None:
    """Write current process PID to file"""
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file(pid_file: Path) -> None:
    """Remove PID file"""
    try:
        pid_file.unlink()
    except FileNotFoundError:
        pass


def is_daemon_running(pid_file: Path | None = None) -> bool:
    """Check if daemon is currently running by checking PID file"""
    if pid_file is None:
        pid_file = get_daemon_pid_file()

    if not pid_file.exists():
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, 0)
        return True

    except Exception:
        remove_pid_file(pid_file)
        return False


def run_daemon(
    host: str = "127.0.0.1",
    port: int = 8000,
    log_file: Path | None = None,
    pid_file: Path | None = None,
) -> None:
    """Run the daemon"""
    if pid_file is None:
        pid_file = get_daemon_pid_file()

    # Check if daemon is already running
    if is_daemon_running(pid_file=pid_file):
        logger.error(f"Daemon already running (PID file: {pid_file})")
        sys.exit(78)  # EX_CONFIG - configuration error

    # Write PID file
    write_pid_file(pid_file)
    logger.info(f"Starting daemon with PID {os.getpid()}")

    try:
        # Create FastAPI app
        app = create_app(log_file)

        logger.info(f"Starting uvicorn server on {host}:{port}")
        uvicorn.run(
            app=app,
            host=host,
            port=port,
            log_config=None,  # Prevent uvicorn from overriding our logging config
        )

    except Exception as e:
        logger.error(f"Daemon failed to start: {e}")
        raise
    finally:
        logger.info("Cleaning up daemon resources...")
        remove_pid_file(pid_file)


def stop_daemon(pid_file: Path | None = None) -> bool:
    """Stop the daemon process"""
    if pid_file is None:
        pid_file = get_daemon_pid_file()

    if not is_daemon_running(pid_file=pid_file):
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Wait up to SHUTDOWN_WAIT_TIME seconds for graceful shutdown
        for _ in range(SHUTDOWN_WAIT_TIME):
            time.sleep(1)
            if not is_daemon_running(pid_file=pid_file):
                return True

        # If still running, force kill
        try:
            os.kill(pid, signal.SIGKILL)
            remove_pid_file(pid_file=pid_file)
            return True
        except Exception:
            return False

    except Exception:
        remove_pid_file(pid_file=pid_file)
        return False


def is_daemon_process_running() -> bool:
    """Check if the daemon process is running"""
    pid_file = get_daemon_pid_file()
    return is_daemon_running(pid_file)
