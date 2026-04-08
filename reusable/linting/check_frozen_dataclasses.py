"""Check that all dataclasses use frozen=True.

Usage: python check_frozen_dataclasses.py [file1.py file2.py ...]
If no files given, scans current directory recursively.

Ignore with: # lint-ignore[unfrozen-dataclass]: <rationale>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from reusable.linting.lint_utils import (
    collect_files,
    has_bare_ignore,
    is_ignored,
    read_source_lines,
    report,
)

CHECK_NAME = "unfrozen-dataclass"


def _has_frozen_true(decorator: ast.expr) -> bool:
    """Check if a decorator node includes frozen=True."""
    if not isinstance(decorator, ast.Call):
        return False
    for kw in decorator.keywords:
        if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _is_dataclass_decorator(decorator: ast.expr) -> bool:
    """Check if a decorator is @dataclass or @dataclass(...)."""
    if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
        return True
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Name) and func.id == "dataclass":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "dataclass":
            return True
    return False


def check_file(path: Path) -> list[str]:
    """Check a single file for unfrozen dataclasses."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        for decorator in node.decorator_list:
            if not _is_dataclass_decorator(decorator):
                continue

            line_num = decorator.lineno
            source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

            if has_bare_ignore(source_line, CHECK_NAME):
                violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
                break

            if is_ignored(source_line, CHECK_NAME):
                break

            if isinstance(decorator, ast.Name) or not _has_frozen_true(decorator):
                violations.append(report(path, line_num, CHECK_NAME, f"dataclass '{node.name}' missing frozen=True"))
            break  # Only check the first matching decorator

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))
    for v in all_violations:
        print(v)
    sys.exit(1 if all_violations else 0)
