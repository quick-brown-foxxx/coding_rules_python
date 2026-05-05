"""Tests for check_type_ignore linting script."""

from __future__ import annotations

from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_type_ignore"


class TestTypeIgnore:
    def test_pass_type_ignore_with_rationale(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_type_ignore_without_rationale(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[type-ignore-rationale]") == 3
        # Verify specific violation line numbers
        assert ":6:" in result.stdout  # type: ignore[assignment] without rationale
        assert ":9:" in result.stdout  # bare type: ignore
        assert ":12:" in result.stdout  # type: ignore[arg-type] without rationale

    def test_valid_ignore_silences_check(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout

    def test_multiple_error_codes_with_and_without_rationale(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_edge_cases.py")
        assert result.returncode == 1
        assert "[type-ignore-rationale]" in result.stdout
        # Only the one without rationale should fail; the one with rationale passes
        assert result.stdout.count("[type-ignore-rationale]") == 1
