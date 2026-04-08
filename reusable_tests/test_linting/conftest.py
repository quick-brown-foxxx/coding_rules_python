"""Shared helpers for linting test files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES: Path = Path(__file__).resolve().parent.parent / "fixtures" / "linting"


@pytest.fixture
def run_linter():
    """Return a helper that runs a linting module against a fixture file."""

    def _run(module: str, fixture: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", module, str(FIXTURES / fixture)],
            capture_output=True,
            text=True,
        )

    return _run
