from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from shared.logging.logger_setup import setup_file_logging, setup_stdout_logging


@pytest.fixture
def isolated_root_logger() -> Iterator[None]:
    """Temporarily isolate root logger handlers for shared logging tests."""
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    original_level = root_logger.level

    root_logger.handlers.clear()
    root_logger.setLevel(logging.NOTSET)

    try:
        yield
    finally:
        for handler in root_logger.handlers:
            handler.close()
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)


def test_stdout_logging_hides_debug_when_level_is_info(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    isolated_root_logger: None,
) -> None:
    """Stdout logging should respect its configured level while file logging keeps DEBUG."""
    setup_file_logging(log_dir=tmp_path, app_name="mockapp")
    setup_stdout_logging(level=logging.INFO)

    logger = logging.getLogger("mockapp.validation")
    logger.debug("debug should only be in file")
    logger.info("info should be in stdout and file")

    captured = capsys.readouterr()
    assert "debug should only be in file" not in captured.out
    assert "info should be in stdout and file" in captured.out

    log_contents = (tmp_path / "mockapp.log").read_text(encoding="utf-8")
    assert "debug should only be in file" in log_contents
    assert "info should be in stdout and file" in log_contents
