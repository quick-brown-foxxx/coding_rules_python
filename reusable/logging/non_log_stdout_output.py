"""Colored stdout output helpers for CLI and scripts.

Provides simple, reusable functions for printing colored messages to stdout/stderr
that are NOT logs. Useful for scripts and CLI tools.

Usage:
    from shared.non_log_stdout_output import write_info, write_error, write_success

    write_info("Starting download...")
    write_success("Download complete!")
    write_error("Failed to download")

Colors:
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - SUCCESS: Green (bright)
"""

from __future__ import annotations

import logging
import sys
from typing import IO

import colorlog

# Cached formatters per stream (I6: avoid recreating on every call)
_formatter_cache: dict[int, colorlog.ColoredFormatter] = {}  # lint-ignore[raw-dict]: internal cache keyed by stream id


def _get_formatter(stream: IO[str]) -> colorlog.ColoredFormatter:
    """Get or create a cached ColoredFormatter for the given stream.

    Args:
        stream: The output stream (e.g. sys.stdout, sys.stderr)

    Returns:
        A ColoredFormatter configured for the stream
    """
    stream_id = id(stream)
    if stream_id not in _formatter_cache:
        _formatter_cache[stream_id] = colorlog.ColoredFormatter(
            "%(log_color)s%(message)s%(reset)s",
            log_colors={
                "INFO": "green",
                "SUCCESS": "green",
                "WARNING": "yellow",
                "ERROR": "red",
            },
            reset=True,
            stream=stream,
        )
    return _formatter_cache[stream_id]


def _get_colored_text(message: str, level: str, stream: IO[str] = sys.stdout) -> str:
    """Get colored version of message.

    Args:
        message: Text to color
        level: Level name ("INFO", "WARNING", "ERROR", "SUCCESS")
        stream: Target stream for color detection (default: sys.stdout)

    Returns:
        Colored text string
    """
    # Map level names to logging module levels
    level_map = {
        "INFO": logging.INFO,
        "SUCCESS": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    log_level = level_map.get(level, logging.INFO)

    formatter = _get_formatter(stream)

    # Create a dummy record with correct level so colors work
    record = logging.LogRecord(
        name="stdout",
        level=log_level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )

    return formatter.format(record)


def write_info(message: str) -> None:
    """Write green info message to stdout.

    Args:
        message: Text to write
    """
    colored = _get_colored_text(message, "INFO")
    sys.stdout.write(f"{colored}\n")


def write_success(message: str) -> None:
    """Write green success message to stdout.

    Args:
        message: Text to write
    """
    colored = _get_colored_text(message, "SUCCESS")
    sys.stdout.write(f"{colored}\n")


def write_warning(message: str) -> None:
    """Write yellow warning message to stdout.

    Args:
        message: Text to write
    """
    colored = _get_colored_text(message, "WARNING")
    sys.stdout.write(f"{colored}\n")


def write_error(message: str) -> None:
    """Write red error message to stderr.

    Args:
        message: Text to write
    """
    colored = _get_colored_text(message, "ERROR", stream=sys.stderr)
    sys.stderr.write(f"{colored}\n")
