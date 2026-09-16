"""Logging setup utilities.

Provides rotating file logging, colored stdout logging, and utilities for
configuring logger levels.

Key principle:
    File logging is always on — it's the durable record for post-mortem debugging.
    Stdout logging is for modes where no human reads stdout directly (GUI, server).
    CLI tools should NOT use stdout logging — use non_log_stdout_output instead,
    so that stdout stays clean for user-facing output (help, prompts, results).
    A CLI tool that needs live logs passes ``stream=sys.stderr`` to
    setup_stdout_logging(), keeping stdout free for user output.

Typical usage patterns:
    - CLI tools: file logging + non_log_stdout_output for user messages
      (+ optional stderr console logging for manual debugging)
    - GUI apps: file logging + stdout logging (dev convenience when launched from terminal)
    - Servers (FastAPI): file logging + stdout logging (container log transport)
    - All modes: silence_noisy_loggers() (or configure_logger_level()) to
      suppress noisy third-party loggers

Usage:
    from pathlib import Path

    import platformdirs

    from shared.logging.logger_setup import (
        setup_stdout_logging,
        setup_file_logging,
        silence_noisy_loggers,
    )

    # Per-OS user dir via platformdirs (don't hardcode ~/.local/state)
    log_dir = Path(platformdirs.user_log_dir("myapp"))

    # CLI tool — file logging only, user messages via write_info/write_error
    setup_file_logging(log_dir=log_dir, app_name="myapp")

    # CLI tool with optional live logs — file logging + stderr console
    setup_file_logging(log_dir=log_dir, app_name="myapp")
    setup_stdout_logging(level=logging.INFO, stream=sys.stderr)

    # GUI app / server — file logging + stdout logging
    setup_file_logging(log_dir=log_dir, app_name="myapp")
    setup_stdout_logging(level=logging.INFO)

    # Suppress noisy third-party loggers
    silence_noisy_loggers()

Stdout output format:
    <colored>2025-12-19 00:01:35 [INFO] module.name:</colored> <default>Log message text</default>

File output format:
    2025-12-19 00:01:35 [INFO] module.name: Log message text

Colors:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red on white background
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final, TextIO

import colorlog

_STDOUT_HANDLER_NAME: Final = "shared.logging.stdout"
_STDERR_HANDLER_NAME: Final = "shared.logging.stderr"
_FILE_HANDLER_PREFIX: Final = "shared.logging.file:"


def _existing_stdout_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if handler.get_name() == _STDOUT_HANDLER_NAME:
            return handler
    return None


def _existing_stderr_handler(root_logger: logging.Logger) -> logging.Handler | None:
    for handler in root_logger.handlers:
        if handler.get_name() == _STDERR_HANDLER_NAME:
            return handler
    return None


def _existing_file_handler(root_logger: logging.Logger, log_path: Path) -> logging.Handler | None:
    handler_name = f"{_FILE_HANDLER_PREFIX}{log_path}"
    for handler in root_logger.handlers:
        if handler.get_name() == handler_name:
            return handler
    return None


def setup_stdout_logging(level: int = logging.INFO, *, stream: TextIO | None = None) -> None:
    """Set up console logging with colored log prefix but uncolored messages.

    Adds a colored StreamHandler to the root logger. Use for GUI apps and servers
    where stdout is not the user interface — it provides dev convenience (see logs
    when launching from terminal) and serves as container log transport.

    Do NOT use for CLI tools — stdout is the user interface there. Use
    non_log_stdout_output (write_info, write_error) for user-facing messages
    instead. A CLI tool that wants live logs during manual runs calls this with
    ``stream=sys.stderr`` so log lines never corrupt stdout output.

    Args:
        level: Logging level to use
        stream: Output stream; defaults to ``sys.stdout``. Pass ``sys.stderr``
            for CLI tools (stdout is the user interface).
    """
    root_logger = logging.getLogger()
    is_stderr = stream is sys.stderr
    handler = _existing_stderr_handler(root_logger) if is_stderr else _existing_stdout_handler(root_logger)
    if handler is None:
        handler = colorlog.StreamHandler(stream if stream is not None else sys.stdout)
        handler.set_name(_STDERR_HANDLER_NAME if is_stderr else _STDOUT_HANDLER_NAME)
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s] %(name)s:%(reset)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                reset=True,
            )
        )
        root_logger.addHandler(handler)
    handler.setLevel(level)
    # Set root level to the lowest of current and requested, so both
    # stdout and file handlers can filter independently
    if root_logger.level == logging.NOTSET or level < root_logger.level:
        root_logger.setLevel(level)


def setup_file_logging(
    log_dir: Path,
    app_name: str = "app",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Set up rotating file logging.

    Adds a RotatingFileHandler to the root logger. File logs are always written
    (at the given level; default INFO). Pass ``level=DEBUG`` to capture
    everything — e.g. the app's AI request/response diagnostics.

    The log file is created at: <log_dir>/<app_name>.log

    Args:
        log_dir: Directory to store log files (created if missing)
        app_name: Name used for the log file (becomes <app_name>.log)
        level: Logging level for the file handler (default: INFO)
        max_bytes: Max size per log file before rotation (default: 5 MB)
        backup_count: Number of rotated log files to keep (default: 3)
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{app_name}.log"

    root_logger = logging.getLogger()
    handler = _existing_file_handler(root_logger, log_path)
    if handler is None:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.set_name(f"{_FILE_HANDLER_PREFIX}{log_path}")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(handler)
    handler.setLevel(level)
    # Set root level to the lowest of current and requested
    if root_logger.level == logging.NOTSET or level < root_logger.level:
        root_logger.setLevel(level)


def configure_logger_level(logger_name: str, level: int, *, propagate: bool = True) -> None:
    """Configure a specific logger's level and propagation.

    Args:
        logger_name: Name of the logger to configure
        level: Logging level to set
        propagate: Whether to propagate to parent loggers
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = propagate


# Third-party HTTP/AI/SQL loggers that emit huge volumes of DEBUG detail (raw
# request dumps, SQL statements, connection churn) — including values like
# ``set-cookie`` tokens — that drown the app's own logs and leak secrets.
# Silenced at WARNING by default; re-enable individually with
# ``configure_logger_level(name, logging.DEBUG)`` when SDK-level debugging is
# needed. Adjust the tuple for your app's dependencies.
_NOISY_LOGGERS: Final = ("httpx", "httpcore", "urllib3", "openai", "anthropic", "aiosqlite")


def silence_noisy_loggers() -> None:
    """Suppress the noisy third-party loggers at WARNING.

    Call from an app entry point (after ``setup_*_logging``) so DEBUG console
    output shows only the app's own logs. The app's own request/response
    logging is unaffected.
    """
    for logger_name in _NOISY_LOGGERS:
        configure_logger_level(logger_name, logging.WARNING)
