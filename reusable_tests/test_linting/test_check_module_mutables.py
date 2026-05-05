"""Tests for check_module_mutables linting script."""

from __future__ import annotations

from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_module_mutables"


class TestModuleMutables:
    def test_pass_valid_module_state(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "mutables_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_mutable_module_state(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "mutables_fail.py")
        assert result.returncode == 1
        assert "[module-mutable-state]" in result.stdout
        # Should catch: list, dict, set, list(), dict()
        assert result.stdout.count("[module-mutable-state]") == 5
        # Verify specific violation line numbers
        assert ":6:" in result.stdout  # _cache: list[str] = []
        assert ":9:" in result.stdout  # registry: dict[str, int] = {}
        assert ":12:" in result.stdout  # seen = set()
        assert ":15:" in result.stdout  # items = list()
        assert ":16:" in result.stdout  # data = dict()

    def test_valid_ignore_silences_check(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "mutables_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "mutables_bare_ignore.py")
        assert result.returncode == 1
        assert "requires rationale" in result.stdout.lower()

    def test_edge_cases_flag_runtime_else_branch_only(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "mutables_edge_cases.py")
        assert result.returncode == 1
        assert "[module-mutable-state]" in result.stdout
        # Should flag defaultdict, OrderedDict, and TYPE_CHECKING else branch only.
        assert result.stdout.count("[module-mutable-state]") == 3
        assert ":10:" in result.stdout
        assert ":13:" in result.stdout
        assert ":21:" in result.stdout
        assert ":18:" not in result.stdout
