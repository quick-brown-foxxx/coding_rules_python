"""Check that `object` is only used in boundary/guard positions.

Flags: dict[str, object], list[object], Sequence[object], tuple[object, ...],
and bare `object` function params (except TypeIs/TypeGuard guards, *args, **kwargs).

Usage: python -m reusable.linting.check_object_annotations [file1.py file2.py ...]
Ignore with: # lint-ignore[restricted-object]: <rationale>
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

CHECK_NAME = "restricted-object"

# Container types where object as a type arg is banned
_BANNED_CONTAINERS = {"dict", "list", "Sequence", "tuple", "set", "frozenset"}


def _is_object_name(node: ast.expr) -> bool:
    """Check if an AST node is the name 'object'."""
    return isinstance(node, ast.Name) and node.id == "object"


def _annotation_has_banned_object(node: ast.expr) -> bool:
    """Check if a type annotation contains banned object usage."""
    # Bare `object`
    if _is_object_name(node):
        return True

    # Subscript: dict[str, object], list[object], etc.
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name) and node.value.id in _BANNED_CONTAINERS:
            # Check type args
            if isinstance(node.slice, ast.Tuple):
                return any(_is_object_name(elt) for elt in node.slice.elts)
            return _is_object_name(node.slice)
        # Recurse into nested subscripts (e.g. Required[dict[str, object]])
        if isinstance(node.slice, ast.Tuple):
            return any(_annotation_has_banned_object(elt) for elt in node.slice.elts)
        return _annotation_has_banned_object(node.slice)

    # BinOp: X | Y union syntax
    if isinstance(node, ast.BinOp):
        return _annotation_has_banned_object(node.left) or _annotation_has_banned_object(node.right)

    return False


def _is_typeis_guard(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function return type is TypeIs[...] or TypeGuard[...]."""
    ret = func.returns
    if ret is None:
        return False
    if isinstance(ret, ast.Subscript) and isinstance(ret.value, ast.Name):
        return ret.value.id in ("TypeIs", "TypeGuard")
    return False


def _is_variadic(arg: ast.arg, func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if arg is *args or **kwargs."""
    variadic_names: set[str] = set()
    if func.args.vararg is not None:
        variadic_names.add(func.args.vararg.arg)
    if func.args.kwarg is not None:
        variadic_names.add(func.args.kwarg.arg)
    return arg.arg in variadic_names


def _is_coroutine_param(node: ast.expr) -> bool:
    """Check if annotation is Coroutine[object, None, T] (first two params allowed)."""
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id == "Coroutine"
    return False


def _check_annotation_violation(
    path: Path,
    source_lines: list[str],
    annotation: ast.expr,
    violations: list[str],
    message: str,
) -> None:
    """Check a single annotation node for banned object usage."""
    line_num = annotation.lineno
    source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

    if has_bare_ignore(source_line, CHECK_NAME):
        violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
        return
    if is_ignored(source_line, CHECK_NAME):
        return

    if _annotation_has_banned_object(annotation):
        violations.append(report(path, line_num, CHECK_NAME, message))


def check_file(path: Path) -> list[str]:
    """Check a single file for restricted object annotations."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []

    for node in ast.walk(tree):
        # Check function annotations
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            is_guard = _is_typeis_guard(node)

            for arg in [*node.args.args, *node.args.posonlyargs, *node.args.kwonlyargs]:
                if arg.annotation is None:
                    continue

                # Skip TypeIs/TypeGuard guard params
                if is_guard and _is_object_name(arg.annotation):
                    continue
                # Skip *args: object, **kwargs: object
                if _is_variadic(arg, node) and _is_object_name(arg.annotation):
                    continue
                # Skip Coroutine[object, None, T] annotations
                if _is_coroutine_param(arg.annotation):
                    continue

                _check_annotation_violation(
                    path,
                    source_lines,
                    arg.annotation,
                    violations,
                    f"restricted 'object' in annotation of '{arg.arg}'",
                )

            # Check return annotation
            if node.returns:
                _check_annotation_violation(
                    path,
                    source_lines,
                    node.returns,
                    violations,
                    f"restricted 'object' in return type of '{node.name}'",
                )

        # Check variable/attribute annotations (class attrs, module-level)
        if isinstance(node, ast.AnnAssign) and node.annotation:
            _check_annotation_violation(
                path,
                source_lines,
                node.annotation,
                violations,
                "restricted 'object' in variable annotation",
            )

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))
    for v in all_violations:
        print(v)
    sys.exit(1 if all_violations else 0)
