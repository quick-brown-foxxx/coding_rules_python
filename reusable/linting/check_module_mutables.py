"""Check for banned module-level mutable state.

Flags module-level assignments creating mutable containers (list, dict, set)
not wrapped in Final. Allows logger assignments and TYPE_CHECKING blocks.

Usage: python -m reusable.linting.check_module_mutables [file1.py file2.py ...]
Ignore with: # lint-ignore[module-mutable-state]: <rationale>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Final

from reusable.linting.lint_utils import (
    collect_files,
    has_bare_ignore,
    is_final_annotation,
    is_ignored,
    read_source_lines,
    report,
)

CHECK_NAME = "module-mutable-state"

# Mutable literal node types
_MUTABLE_LITERALS = (ast.List, ast.Dict, ast.Set)

# Mutable constructor function names
_MUTABLE_CONSTRUCTORS: Final = frozenset({"list", "dict", "set", "defaultdict", "OrderedDict"})

# Logger function names (allowed)
_LOGGER_FUNCS: Final = frozenset({"getLogger"})


def _is_logger_call(value: ast.expr) -> bool:
    """Check if value is a getLogger(...) or logging.getLogger(...) call."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name) and func.id in _LOGGER_FUNCS:
        return True
    return isinstance(func, ast.Attribute) and func.attr in _LOGGER_FUNCS


def _is_mutable_value(value: ast.expr) -> bool:
    """Check if a value creates a mutable container."""
    if isinstance(value, _MUTABLE_LITERALS):
        return True
    if isinstance(value, ast.Call):
        func = value.func
        if isinstance(func, ast.Name) and func.id in _MUTABLE_CONSTRUCTORS:
            return True
        if isinstance(func, ast.Attribute) and func.attr in _MUTABLE_CONSTRUCTORS:
            return True
    return False


def _in_type_checking_block(node: ast.stmt, tree: ast.Module) -> bool:
    """Check if a statement is inside an `if TYPE_CHECKING:` block."""
    for top_node in tree.body:
        if isinstance(top_node, ast.If):
            test = top_node.test
            if (
                isinstance(test, ast.Name)
                and test.id == "TYPE_CHECKING"
                and (node in top_node.body or node in top_node.orelse)
            ):
                return True
    return False


def _check_mutable_assignment(
    node: ast.stmt,
    value: ast.expr,
    path: Path,
    source_lines: list[str],
    violations: list[str],
) -> None:
    """Check a module-level assignment for mutable state."""
    if _is_logger_call(value):
        return
    if not _is_mutable_value(value):
        return

    line_num = node.lineno
    source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""
    if has_bare_ignore(source_line, CHECK_NAME):
        violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
    elif not is_ignored(source_line, CHECK_NAME):
        violations.append(
            report(path, line_num, CHECK_NAME, "module-level mutable state — use Final or move into a class/function")
        )


def check_file(path: Path) -> list[str]:
    """Check a single file for module-level mutable state."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []

    for node in tree.body:
        # Skip if inside TYPE_CHECKING block
        if _in_type_checking_block(node, tree):
            continue

        # Handle annotated assignments: x: list[str] = []
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            if is_final_annotation(node.annotation):
                continue
            _check_mutable_assignment(node, node.value, path, source_lines, violations)

        # Handle plain assignments: x = [] or x = dict()
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            # Skip dunder assignments (__all__, __version__, etc.)
            if isinstance(target, ast.Name) and target.id.startswith("__") and target.id.endswith("__"):
                continue
            _check_mutable_assignment(node, node.value, path, source_lines, violations)

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))
    for v in all_violations:
        print(v)
    sys.exit(1 if all_violations else 0)
