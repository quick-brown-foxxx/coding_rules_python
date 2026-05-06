"""Tests for check_ignored_results linting script."""

from __future__ import annotations

from shared_tests.test_linting.conftest import RunLinter

MODULE = "shared.linting.check_ignored_results"
EXPECTED_VIOLATION_COUNT = 2
EXPECTED_IMPORTED_VIOLATION_COUNT = 6


class TestIgnoredResults:
    def test_fail_ignored_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_fail.py")

        assert result.returncode == 1
        assert result.stdout.count("[ignored-result]") == EXPECTED_VIOLATION_COUNT
        assert ":17:" in result.stdout
        assert ":18:" in result.stdout

    def test_pass_handled_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_pass.py")

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_bare_ignore.py")

        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()

    def test_fail_alias_and_imported_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_imports/consumer.py")

        assert result.returncode == 1
        assert result.stdout.count("[ignored-result]") == EXPECTED_IMPORTED_VIOLATION_COUNT
        assert ":18:" in result.stdout
        assert ":19:" in result.stdout
        assert ":20:" in result.stdout
        assert ":21:" in result.stdout
        assert ":22:" in result.stdout
        assert ":23:" in result.stdout

    def test_pass_handled_imported_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_imports/pass_consumer.py")

        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_relative_imported_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_imports/relpkg/consumer.py")

        assert result.returncode == 1
        assert ":9:" in result.stdout

    def test_fail_reexported_package_result_calls(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "ignored_results_imports/reexport_package.py")

        assert result.returncode == 1
        assert ":9:" in result.stdout
