"""Tests for check_ignored_results linting script."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from shared_tests.test_linting.conftest import RunLinter, RunLinterPath

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

    def test_absolute_import_does_not_resolve_nearby_ancestor_module(
        self,
        tmp_path: Path,
        run_linter_path: RunLinterPath,
    ) -> None:
        pkg_dir = tmp_path / "pkg"
        sub_dir = pkg_dir / "sub"
        sub_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        (sub_dir / "__init__.py").write_text("", encoding="utf-8")
        (pkg_dir / "helper.py").write_text(
            dedent(
                """
                from rusty_results import Ok, Result

                def local_result() -> Result[int, str]:
                    return Ok(1)
                """
            ),
            encoding="utf-8",
        )
        consumer = sub_dir / "consumer.py"
        consumer.write_text(
            dedent(
                """
                import helper

                helper.local_result()
                """
            ),
            encoding="utf-8",
        )

        result = run_linter_path(MODULE, consumer)

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""

    def test_qualified_non_rusty_result_annotation_does_not_trigger(
        self,
        tmp_path: Path,
        run_linter_path: RunLinterPath,
    ) -> None:
        source_path = tmp_path / "foreign_result.py"
        source_path.write_text(
            dedent(
                """
                class api:
                    class Result[T]:
                        pass


                def foreign_result() -> api.Result[int]:
                    return api.Result()


                foreign_result()
                """
            ),
            encoding="utf-8",
        )

        result = run_linter_path(MODULE, source_path)

        assert result.returncode == 0, result.stdout
        assert result.stdout.strip() == ""

    def test_bare_result_annotation_is_checked(self, tmp_path: Path, run_linter_path: RunLinterPath) -> None:
        source_path = tmp_path / "bare_result.py"
        source_path.write_text(
            dedent(
                """
                from rusty_results import Ok, Result


                def bare_result() -> Result:
                    return Ok(1)


                bare_result()
                """
            ),
            encoding="utf-8",
        )

        result = run_linter_path(MODULE, source_path)

        assert result.returncode == 1
        assert "ignored Result return from 'bare_result'" in result.stdout

    def test_src_layout_imported_result_call_is_checked(self, tmp_path: Path, run_linter_path: RunLinterPath) -> None:
        src_dir = tmp_path / "src" / "todo_package_name"
        tests_dir = tmp_path / "tests"
        src_dir.mkdir(parents=True)
        tests_dir.mkdir()
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (src_dir / "service.py").write_text(
            dedent(
                """
                from rusty_results import Ok, Result


                def compute() -> Result[int, str]:
                    return Ok(1)
                """
            ),
            encoding="utf-8",
        )
        test_path = tests_dir / "test_service.py"
        test_path.write_text(
            dedent(
                """
                from todo_package_name.service import compute


                def test_probe() -> None:
                    compute()
                """
            ),
            encoding="utf-8",
        )

        result = run_linter_path(MODULE, test_path)

        assert result.returncode == 1
        assert "ignored Result return from 'compute'" in result.stdout

    def test_src_package_can_resolve_repo_root_shared_imports(
        self,
        tmp_path: Path,
        run_linter_path: RunLinterPath,
    ) -> None:
        src_dir = tmp_path / "src" / "todo_package_name"
        shared_dir = tmp_path / "shared"
        src_dir.mkdir(parents=True)
        shared_dir.mkdir()
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (shared_dir / "helpers.py").write_text(
            dedent(
                """
                from rusty_results import Ok, Result


                def compute() -> Result[int, str]:
                    return Ok(1)
                """
            ),
            encoding="utf-8",
        )
        consumer = src_dir / "consumer.py"
        consumer.write_text(
            dedent(
                """
                import shared.helpers


                def run() -> None:
                    shared.helpers.compute()
                """
            ),
            encoding="utf-8",
        )

        result = run_linter_path(MODULE, consumer)

        assert result.returncode == 1
        assert "ignored Result return from 'shared.helpers.compute'" in result.stdout
