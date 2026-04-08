"""Check for raw dict[K, V] type annotations in domain/business code.

Flags raw ``dict[K, V]`` subscript annotations in function parameters,
return types, class attributes, and module-level variables.
Allowed: Final[dict[...]], annotations inside function bodies (local
variables are transient), **kwargs typing, and bare ``dict`` without subscript.

Usage: python -m reusable.linting.check_raw_dicts [file1.py file2.py ...]
Ignore with: # lint-ignore[raw-dict]: <rationale>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from reusable.linting.lint_utils import (
    collect_files,
    has_bare_ignore,
    is_final_annotation,
    is_ignored,
    read_source_lines,
    report,
)

CHECK_NAME = "raw-dict"


def _contains_raw_dict(node: ast.expr) -> bool:
    """Recursively check whether *node* contains a ``dict[K, V]`` subscript."""
    # dict[K, V] — the direct case
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name) and node.value.id == "dict":
            return True
        # Recurse into wrapper subscripts like Required[dict[str, str]]
        if isinstance(node.slice, ast.Tuple):
            return any(_contains_raw_dict(elt) for elt in node.slice.elts)
        return _contains_raw_dict(node.slice)

    # X | dict[str, str] union syntax
    if isinstance(node, ast.BinOp):
        return _contains_raw_dict(node.left) or _contains_raw_dict(node.right)

    return False


def _check_annotation(
    path: Path,
    source_lines: list[str],
    annotation: ast.expr,
    violations: list[str],
    message: str,
) -> None:
    """Check a single annotation for raw dict usage, respecting ignore comments."""
    line_num = annotation.lineno
    source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

    if has_bare_ignore(source_line, CHECK_NAME):
        violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
        return
    if is_ignored(source_line, CHECK_NAME):
        return

    if _contains_raw_dict(annotation):
        violations.append(report(path, line_num, CHECK_NAME, message))


def _check_function(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    path: Path,
    source_lines: list[str],
    violations: list[str],
) -> None:
    """Check function parameter and return annotations (but NOT body AnnAssigns)."""
    # Check parameter annotations (skip **kwargs)
    kwarg_name = func.args.kwarg.arg if func.args.kwarg is not None else None
    for arg in [*func.args.args, *func.args.posonlyargs, *func.args.kwonlyargs]:
        if arg.annotation is None:
            continue
        if arg.arg == kwarg_name:
            continue
        _check_annotation(
            path,
            source_lines,
            arg.annotation,
            violations,
            f"raw dict annotation in parameter '{arg.arg}' — use TypedDict or dataclass",
        )

    # Check return type
    if func.returns is not None:
        _check_annotation(
            path,
            source_lines,
            func.returns,
            violations,
            f"raw dict annotation in return type of '{func.name}' — use TypedDict or dataclass",
        )


def check_file(path: Path) -> list[str]:
    """Check a single file for raw dict annotations."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []

    # Walk module body manually (NOT ast.walk) to distinguish module-level
    # and class-level AnnAssign from function-local ones.
    for node in tree.body:
        # Module-level annotated assignment
        if isinstance(node, ast.AnnAssign) and node.annotation and not is_final_annotation(node.annotation):
            _check_annotation(
                path,
                source_lines,
                node.annotation,
                violations,
                "raw dict annotation at module level — use TypedDict or dataclass",
            )

        # Functions at module level
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            _check_function(node, path, source_lines, violations)

        # Classes — check class body for attribute annotations and methods
        if isinstance(node, ast.ClassDef):
            for class_node in node.body:
                if (
                    isinstance(class_node, ast.AnnAssign)
                    and class_node.annotation
                    and not is_final_annotation(class_node.annotation)
                ):
                    _check_annotation(
                        path,
                        source_lines,
                        class_node.annotation,
                        violations,
                        "raw dict annotation in class attribute — use TypedDict or dataclass",
                    )
                if isinstance(class_node, ast.FunctionDef | ast.AsyncFunctionDef):
                    _check_function(class_node, path, source_lines, violations)

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))
    for v in all_violations:
        print(v)
    sys.exit(1 if all_violations else 0)
