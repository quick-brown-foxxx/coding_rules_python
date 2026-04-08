"""Tests for check_raw_dicts linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MODULE = "reusable.linting.check_raw_dicts"
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestRawDicts:
    def test_pass_no_raw_dicts(self) -> None:
        result = _run("raw_dicts_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_raw_dict_annotations(self) -> None:
        result = _run("raw_dicts_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[raw-dict]") == 4

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("raw_dicts_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("raw_dicts_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout
