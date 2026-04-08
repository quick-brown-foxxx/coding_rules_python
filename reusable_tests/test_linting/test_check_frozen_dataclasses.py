"""Tests for check_frozen_dataclasses linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MODULE = "reusable.linting.check_frozen_dataclasses"
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestFrozenDataclasses:
    def test_pass_frozen_dataclasses(self) -> None:
        result = _run("frozen_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_unfrozen_dataclasses(self) -> None:
        result = _run("frozen_fail.py")
        assert result.returncode == 1
        assert "[unfrozen-dataclass]" in result.stdout
        # Should catch all 3 unfrozen classes
        assert result.stdout.count("[unfrozen-dataclass]") == 3

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("frozen_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("frozen_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[unfrozen-dataclass]" in result.stdout
