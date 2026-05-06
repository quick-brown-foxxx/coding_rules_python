"""Tests for check_frozen_dataclasses linting script."""

from __future__ import annotations

from shared_tests.test_linting.conftest import RunLinter

MODULE = "shared.linting.check_frozen_dataclasses"


class TestFrozenDataclasses:
    def test_pass_frozen_dataclasses(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "frozen_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_unfrozen_dataclasses(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "frozen_fail.py")
        assert result.returncode == 1
        assert "[unfrozen-dataclass]" in result.stdout
        # Should catch all 3 unfrozen classes
        assert result.stdout.count("[unfrozen-dataclass]") == 3
        # Verify specific violation line numbers
        assert ":6:" in result.stdout  # UnfrozenSimple
        assert ":11:" in result.stdout  # UnfrozenWithSlots
        assert ":17:" in result.stdout  # ExplicitlyUnfrozen

    def test_valid_ignore_silences_check(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "frozen_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "frozen_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()

    def test_fail_qualified_and_nested_dataclasses(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "frozen_edge_cases.py")
        assert result.returncode == 1
        assert "[unfrozen-dataclass]" in result.stdout
        # Should catch: qualified no-parens, qualified with slots, nested inner class
        assert result.stdout.count("[unfrozen-dataclass]") == 3
