"""Tests for check_raw_dicts linting script."""

from __future__ import annotations

MODULE = "reusable.linting.check_raw_dicts"


class TestRawDicts:
    def test_pass_no_raw_dicts(self, run_linter) -> None:
        result = run_linter(MODULE, "raw_dicts_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_raw_dict_annotations(self, run_linter) -> None:
        result = run_linter(MODULE, "raw_dicts_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[raw-dict]") == 4

    def test_valid_ignore_silences_check(self, run_linter) -> None:
        result = run_linter(MODULE, "raw_dicts_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter) -> None:
        result = run_linter(MODULE, "raw_dicts_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout
