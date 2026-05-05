"""Tests for check_module_mutables linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from reusable.linting.check_module_mutables import check_file
from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_module_mutables"


class TestModuleMutables:
    def test_regression_formatter_cache_needs_ignore(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                MODULE,
                str(repo_root / "reusable" / "logging" / "non_log_stdout_output.py"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""

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

    def test_qualified_typing_type_checking_checks_runtime_else(self, tmp_path: Path) -> None:
        path = tmp_path / "mutables_qualified_type_checking.py"
        path.write_text(
            "import typing\n\nif typing.TYPE_CHECKING:\n    type_only = {}\nelse:\n    runtime_value = {}\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert len(violations) == 1
        assert "[module-mutable-state]" in violations[0]
        assert ":5:" in violations[0]
