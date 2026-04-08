"""Tests for check_module_mutables linting script."""

from __future__ import annotations

MODULE = "reusable.linting.check_module_mutables"


class TestModuleMutables:
    def test_pass_valid_module_state(self, run_linter) -> None:
        result = run_linter(MODULE, "mutables_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_mutable_module_state(self, run_linter) -> None:
        result = run_linter(MODULE, "mutables_fail.py")
        assert result.returncode == 1
        assert "[module-mutable-state]" in result.stdout
        # Should catch: list, dict, set, list(), dict()
        assert result.stdout.count("[module-mutable-state]") == 5

    def test_valid_ignore_silences_check(self, run_linter) -> None:
        result = run_linter(MODULE, "mutables_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter) -> None:
        result = run_linter(MODULE, "mutables_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()
