"""Tests for check_object_annotations linting script."""

from __future__ import annotations

from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_object_annotations"


class TestObjectAnnotations:
    def test_pass_valid_object_uses(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_banned_object_uses(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_fail.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Should catch: dict[str, object], list[object], bare object param, TypedDict field
        assert result.stdout.count("[restricted-object]") == 4
        # Verify specific violation line numbers
        assert ":9:" in result.stdout  # dict[str, object] return type
        assert ":14:" in result.stdout  # list[object] return type
        assert ":19:" in result.stdout  # bare object param
        assert ":25:" in result.stdout  # TypedDict field with dict[str, object]

    def test_valid_ignore_silences_check(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()

    def test_variadic_object_allowed_sequence_object_flagged(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_edge_cases.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Only Sequence[object] return type should be flagged; *args and **kwargs pass
        assert result.stdout.count("[restricted-object]") == 1
        assert "get_items" in result.stdout
