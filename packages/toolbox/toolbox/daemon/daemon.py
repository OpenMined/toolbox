import os
import signal
import sys
import time
from pathlib import Path

import uvicorn
from loguru import logger

from toolbox.daemon.app import create_app
from toolbox.daemon.daemon_logging import setup_logging
from toolbox.settings import settings

SHUTDOWN_WAIT_TIME = 10  # Maximum time to wait for graceful shutdown in seconds


def write_pid_file(pid_file: Path) -> None:
    """Write current process PID to file"""
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file(pid_file: Path) -> None:
    pid_file.unlink(missing_ok=True)


def is_daemon_running(pid_file: Path | None = None) -> bool:
    """Check if daemon is currently running by checking PID file"""
    if pid_file is None:
        pid_file = settings.daemon.pid_file

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
    host: str | None = None,
    port: int | None = None,
    log_file: Path | None = None,
    pid_file: Path | None = None,
    log_to_file: bool = True,
) -> None:
    """Run the daemon"""

    # Apply overrides
    if host is not None:
        settings.daemon.host = host
    if port is not None:
        settings.daemon.port = port
    if log_file is not None:
        settings.daemon.log_file = log_file
    if not log_to_file:
        settings.daemon.log_file = None
    if pid_file is not None:
        settings.daemon.pid_file = pid_file

    if is_daemon_running(pid_file=settings.daemon.pid_file):
        logger.error(f"Daemon already running (PID file: {settings.daemon.pid_file})")
        sys.exit(78)  # EX_CONFIG - configuration error

    write_pid_file(settings.daemon.pid_file)
    logger.info(f"Starting daemon with PID {os.getpid()}")

    try:
        # Create FastAPI app with settings
        if settings.daemon.log_file:
            logger.info(f"Logging to file: {settings.daemon.log_file}")
        setup_logging(settings.daemon.log_file)

        app = create_app(settings=settings.daemon)

        logger.info(
            f"Starting uvicorn server on {settings.daemon.host}:{settings.daemon.port}"
        )
        uvicorn.run(
            app=app,
            host=settings.daemon.host,
            port=settings.daemon.port,
            log_config=None,  # Prevent uvicorn from overriding logging config
        )

    except Exception as e:
        logger.error(f"Daemon failed to start: {e}")
        raise
    finally:
        remove_pid_file(settings.daemon.pid_file)


def stop_daemon(pid_file: Path | None = None) -> bool:
    """Stop the daemon process"""
    if pid_file is None:
        pid_file = settings.daemon.pid_file

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
