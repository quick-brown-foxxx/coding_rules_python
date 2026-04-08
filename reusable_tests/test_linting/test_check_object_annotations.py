"""Tests for check_object_annotations linting script."""

from __future__ import annotations

MODULE = "reusable.linting.check_object_annotations"


class TestObjectAnnotations:
    def test_pass_valid_object_uses(self, run_linter) -> None:
        result = run_linter(MODULE, "object_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_banned_object_uses(self, run_linter) -> None:
        result = run_linter(MODULE, "object_fail.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Should catch: dict[str, object], list[object], bare object param, TypedDict field
        assert result.stdout.count("[restricted-object]") == 4

    def test_valid_ignore_silences_check(self, run_linter) -> None:
        result = run_linter(MODULE, "object_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter) -> None:
        result = run_linter(MODULE, "object_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()
