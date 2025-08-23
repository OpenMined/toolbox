import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """Handler to intercept standard logging and redirect to loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a logging record to loguru"""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_file: Path | None = None, log_level: str = "DEBUG") -> None:
    """
    Configure unified logging for the application.

    This sets up loguru to intercept all logs from uvicorn, FastAPI, and other
    libraries that use Python's standard logging module.

    Args:
        log_file: Optional path to log file for persistent logging
        log_level: Logging level (default: INFO)
    """
    # Remove all existing loguru handlers
    logger.remove()

    # Add file handler if log_file is provided, otherwise console
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="10 MB",
            retention=1,  # Keep only the current file
        )
    else:
        # Only add console handler if no log file is provided
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    # Create intercept handler
    intercept_handler = InterceptHandler()

    # Configure logging for uvicorn and FastAPI
    # These loggers need to be explicitly configured as they don't appear in root logger
    loggers_to_intercept = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "starlette",
        "starlette.applications",
    ]

    for logger_name in loggers_to_intercept:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [intercept_handler]
        logging_logger.setLevel(log_level)
        logging_logger.propagate = False

    # Also configure root logger to catch any other logs
    logging.root.handlers = [intercept_handler]
    logging.root.setLevel(log_level)

    logger.info(f"Unified logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")
