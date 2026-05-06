"""Tests for check_object_annotations linting script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from reusable.linting.check_object_annotations import check_file
from reusable_tests.test_linting.conftest import RunLinter

MODULE = "reusable.linting.check_object_annotations"


class TestObjectAnnotations:
    def test_regression_shortcuts_helpers_need_explicit_ignore(self) -> None:
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

    def test_edge_cases_only_allow_exact_coroutine_shape(self, run_linter: RunLinter) -> None:
        result = run_linter(MODULE, "object_edge_cases.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Sequence[object] plus non-exempt Coroutine[...] shapes should fail.
        assert result.stdout.count("[restricted-object]") == 4
        assert "get_items" in result.stdout
        assert "first_coro" in result.stdout
        assert "send_coro" in result.stdout
        assert "return_coro" in result.stdout
        assert "allowed_coro" not in result.stdout

    def test_mixed_bare_ignore_still_fails_for_relevant_check(self, tmp_path: Path) -> None:
        path = tmp_path / "bare_ignore_combo.py"
        path.write_text(
            "value: dict[str, object] | None = None  "
            "# lint-ignore[restricted-object]  "
            "# lint-ignore[raw-dict]: raw-dict rationale only\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert violations == [f"{path}:1: [restricted-object] lint-ignore requires rationale after ':'"]

    def test_nested_object_inside_container_is_reported(self, tmp_path: Path) -> None:
        path = tmp_path / "nested_object.py"
        path.write_text(
            "def bad_nested() -> list[tuple[object, str]]:\n    return []\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert violations == [f"{path}:1: [restricted-object] restricted 'object' in return type of 'bad_nested'"]

    def test_exact_allowed_coroutine_shape_is_allowed_beyond_parameters(self, tmp_path: Path) -> None:
        path = tmp_path / "allowed_coroutine_positions.py"
        path.write_text(
            "from collections.abc import Coroutine\n\n"
            "def produce() -> Coroutine[object, None, str]:\n"
            "    raise NotImplementedError\n\n"
            "value: Coroutine[object, None, str] | None = None\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert violations == []

    def test_qualified_type_guards_are_allowed(self, tmp_path: Path) -> None:
        path = tmp_path / "qualified_type_guards.py"
        path.write_text(
            "from typing import TypeGuard\n"
            "import typing\n\n"
            "class MyConfig:\n"
            "    name: str\n\n"
            "def is_config(value: object) -> typing.TypeGuard[MyConfig]:\n"
            "    return isinstance(value, MyConfig)\n\n"
            "def is_config_direct(value: object) -> TypeGuard[MyConfig]:\n"
            "    return isinstance(value, MyConfig)\n",
            encoding="utf-8",
        )

        violations = check_file(path)

        assert violations == []
