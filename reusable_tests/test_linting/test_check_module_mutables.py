"""Tests for check_module_mutables linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MODULE = "reusable.linting.check_module_mutables"
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestModuleMutables:
    def test_pass_valid_module_state(self) -> None:
        result = _run("mutables_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_mutable_module_state(self) -> None:
        result = _run("mutables_fail.py")
        assert result.returncode == 1
        assert "[module-mutable-state]" in result.stdout
        # Should catch: list, dict, set, list(), dict()
        assert result.stdout.count("[module-mutable-state]") >= 4

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("mutables_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("mutables_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[module-mutable-state]" in result.stdout
