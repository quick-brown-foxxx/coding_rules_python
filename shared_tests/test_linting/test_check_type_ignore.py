"""Tests for check_type_ignore linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shared_tests.test_linting.conftest import RunLinter

MODULE = "shared.linting.check_type_ignore"


class TestTypeIgnore:
    def test_regression_linter_tests_do_not_self_trigger(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                MODULE,
                str(repo_root / "shared_tests" / "test_linting" / "test_check_type_ignore.py"),
                str(repo_root / "shared_tests" / "test_linting" / "test_lint_utils.py"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""

    def test_pass_type_ignore_with_rationale(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_type_ignore_without_rationale(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "type_ignore_fail.py")
        assert result.returncode == 1
        assert result.stdout.count("[type-ignore-rationale]") == 3
        # Verify specific violation line numbers
        assert ":6:" in result.stdout  # assignment-ignore fixture line
        assert ":9:" in result.stdout  # bare-ignore fixture line
        assert ":12:" in result.stdout  # arg-type-ignore fixture line

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

    def test_non_directive_text_does_not_trigger(self, tmp_path: Path) -> None:
        path = tmp_path / "type_ignore_text_only.py"
        path.write_text(
            'MESSAGE = "not a directive"  # type: ignored by docs\n',
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, "-m", MODULE, str(path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""
