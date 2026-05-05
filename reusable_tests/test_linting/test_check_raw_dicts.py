"""Tests for check_raw_dicts linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from reusable.linting.check_raw_dicts import check_file
from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_raw_dicts"


class TestRawDicts:
    def test_regression_shortcuts_helpers_need_raw_dict_ignore(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                MODULE,
                str(repo_root / "reusable" / "shortcuts" / "shortcuts.py"),
                str(repo_root / "reusable_tests" / "test_shortcuts_base.py"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""

    def test_pass_no_raw_dicts(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "raw_dicts_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_raw_dict_annotations(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "raw_dicts_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[raw-dict]") == 4
        # Verify specific violation line numbers
        assert ":7:" in result.stdout  # dict param
        assert ":12:" in result.stdout  # dict return type
        assert ":18:" in result.stdout  # dict class attribute
        assert ":22:" in result.stdout  # dict module-level annotation

    def test_valid_ignore_silences_check(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "raw_dicts_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "raw_dicts_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale" in result.stdout

    def test_fail_nested_dict_and_union_dict(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "raw_dicts_edge_cases.py")
        assert result.returncode == 1
        assert "[raw-dict]" in result.stdout
        # Nested dict return type and dict in union param
        assert result.stdout.count("[raw-dict]") == 2

    def test_bare_ignore_reports_once_for_relevant_annotation(self, tmp_path: Path) -> None:
        path = tmp_path / "raw_dicts_bare_single.py"
        path.write_text(
            "def bare_ignored_param(data: dict[str, str]) -> None:  # lint-ignore[raw-dict]\n    _ = data\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert violations == [f"{path}:1: [raw-dict] lint-ignore requires rationale after ':'"]
