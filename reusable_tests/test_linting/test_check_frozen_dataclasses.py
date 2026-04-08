"""Tests for check_frozen_dataclasses linting script."""

from __future__ import annotations

MODULE = "reusable.linting.check_frozen_dataclasses"


class TestFrozenDataclasses:
    def test_pass_frozen_dataclasses(self, run_linter) -> None:
        result = run_linter(MODULE, "frozen_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_unfrozen_dataclasses(self, run_linter) -> None:
        result = run_linter(MODULE, "frozen_fail.py")
        assert result.returncode == 1
        assert "[unfrozen-dataclass]" in result.stdout
        # Should catch all 3 unfrozen classes
        assert result.stdout.count("[unfrozen-dataclass]") == 3

    def test_valid_ignore_silences_check(self, run_linter) -> None:
        result = run_linter(MODULE, "frozen_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter) -> None:
        result = run_linter(MODULE, "frozen_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()
