"""Tests for file-level ignores shared by custom linting scripts."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared_tests.test_linting.conftest import RunLinterPath


@pytest.mark.parametrize(
    ("module", "check_name", "source"),
    [
        (
            "shared.linting.check_object_annotations",
            "restricted-object",
            "# lint-ignore-file[restricted-object]: boundary fixture\nVALUE: object = 1\n",
        ),
        (
            "shared.linting.check_module_mutables",
            "module-mutable-state",
            "# lint-ignore-file[module-mutable-state]: legacy cache\nCACHE = []\n",
        ),
        (
            "shared.linting.check_raw_dicts",
            "raw-dict",
            "# lint-ignore-file[raw-dict]: compatibility shim\nDATA: dict[str, str] = {}\n",
        ),
        (
            "shared.linting.check_frozen_dataclasses",
            "unfrozen-dataclass",
            "# lint-ignore-file[unfrozen-dataclass]: framework model\n"
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class User:\n"
            "    name: str\n",
        ),
        (
            "shared.linting.check_type_ignore",
            "type-ignore-rationale",
            "# lint-ignore-file[type-ignore-rationale]: third-party stub gap\nVALUE = 1  # type: ignore[assignment]\n",
        ),
        (
            "shared.linting.check_ignored_results",
            "ignored-result",
            "# lint-ignore-file[ignored-result]: transitional module\n"
            "from rusty_results import Ok, Result\n\n"
            "def compute() -> Result[int, str]:\n"
            "    return Ok(1)\n\n"
            "compute()\n",
        ),
    ],
)
def test_file_level_ignore_suppresses_each_custom_linter(
    tmp_path: Path,
    module: str,
    check_name: str,
    source: str,
    run_linter_path: RunLinterPath,
) -> None:
    source_path = tmp_path / f"{check_name}.py"
    source_path.write_text(source, encoding="utf-8")

    result = run_linter_path(module, source_path)

    assert result.returncode == 0, result.stdout
    assert result.stdout.strip() == ""


def test_file_level_ignore_requires_rationale(tmp_path: Path, run_linter_path: RunLinterPath) -> None:
    source_path = tmp_path / "bare_file_ignore.py"
    source_path.write_text(
        "# lint-ignore-file[module-mutable-state]\nCACHE = []\n",
        encoding="utf-8",
    )

    result = run_linter_path("shared.linting.check_module_mutables", source_path)

    assert result.returncode == 1
    assert "lint-ignore-file requires rationale" in result.stdout


def test_file_level_ignore_text_inside_docstring_does_not_suppress_check(
    tmp_path: Path,
    run_linter_path: RunLinterPath,
) -> None:
    source_path = tmp_path / "docstring_example.py"
    source_path.write_text(
        '"""Example only: # lint-ignore-file[module-mutable-state]: docs"""\nCACHE = []\n',
        encoding="utf-8",
    )

    result = run_linter_path("shared.linting.check_module_mutables", source_path)

    assert result.returncode == 1
    assert "module-level mutable state" in result.stdout
