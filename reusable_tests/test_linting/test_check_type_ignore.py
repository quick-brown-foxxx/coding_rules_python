"""Tests for check_type_ignore linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MODULE = "reusable.linting.check_type_ignore"
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestTypeIgnore:
    def test_pass_type_ignore_with_rationale(self) -> None:
        result = _run("type_ignore_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_type_ignore_without_rationale(self) -> None:
        result = _run("type_ignore_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[type-ignore-rationale]") == 3

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("type_ignore_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("type_ignore_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout
