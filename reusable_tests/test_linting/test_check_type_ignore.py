"""Tests for check_type_ignore linting script."""

from __future__ import annotations

MODULE = "reusable.linting.check_type_ignore"


class TestTypeIgnore:
    def test_pass_type_ignore_with_rationale(self, run_linter) -> None:
        result = run_linter(MODULE, "type_ignore_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_type_ignore_without_rationale(self, run_linter) -> None:
        result = run_linter(MODULE, "type_ignore_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[type-ignore-rationale]") == 3

    def test_valid_ignore_silences_check(self, run_linter) -> None:
        result = run_linter(MODULE, "type_ignore_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter) -> None:
        result = run_linter(MODULE, "type_ignore_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout
