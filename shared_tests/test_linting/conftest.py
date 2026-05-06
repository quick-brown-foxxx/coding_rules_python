"""Shared helpers for linting test files."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

FIXTURES: Path = Path(__file__).resolve().parent.parent / "fixtures" / "linting"

type RunLinter = Callable[[str, str], subprocess.CompletedProcess[str]]
type RunLinterPath = Callable[[str, Path], subprocess.CompletedProcess[str]]


@pytest.fixture
def run_linter() -> RunLinter:
    """Return a helper that runs a linting module against a fixture file."""

    def _run(module: str, fixture: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", module, str(FIXTURES / fixture)],
            capture_output=True,
            text=True,
        )

    return _run


@pytest.fixture
def run_linter_path() -> RunLinterPath:
    """Return a helper that runs a linting module against an explicit path."""

    def _run(module: str, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", module, str(path)],
            capture_output=True,
            text=True,
        )

    return _run
