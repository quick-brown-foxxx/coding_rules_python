"""Tests for check_object_annotations linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MODULE = "reusable.linting.check_object_annotations"
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestObjectAnnotations:
    def test_pass_valid_object_uses(self) -> None:
        result = _run("object_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_banned_object_uses(self) -> None:
        result = _run("object_fail.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Should catch: dict[str, object], list[object], bare object param, TypedDict field
        assert result.stdout.count("[restricted-object]") >= 3

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("object_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("object_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[restricted-object]" in result.stdout
