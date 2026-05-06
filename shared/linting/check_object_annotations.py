"""Check that `object` is only used in boundary/guard positions.

Flags: dict[str, object], list[object], Sequence[object], tuple[object, ...],
and bare `object` function params (except TypeIs/TypeGuard guards, *args, **kwargs).

Usage: python -m shared.linting.check_object_annotations [file1.py file2.py ...]
Ignore with: # lint-ignore[restricted-object]: <rationale>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Final

from shared.linting.lint_utils import collect_files, has_bare_ignore, is_ignored, read_source_lines, report

CHECK_NAME = "restricted-object"
_COROUTINE_ARG_COUNT = 3

# Container types where object as a type arg is banned
_BANNED_CONTAINERS: Final = frozenset({"dict", "list", "Sequence", "tuple", "set", "frozenset"})


def _is_object_name(node: ast.expr) -> bool:
    """Check if an AST node is the name 'object'."""
    return isinstance(node, ast.Name) and node.id == "object"


def _is_coroutine_annotation(node: ast.expr) -> bool:
    """Check if annotation refers to Coroutine[...] in name or attribute form."""
    if not isinstance(node, ast.Subscript):
        return False

    value = node.value
    if isinstance(value, ast.Name):
        return value.id == "Coroutine"
    if isinstance(value, ast.Attribute):
        return value.attr == "Coroutine"
    return False


def _is_allowed_coroutine_object(node: ast.expr) -> bool:
    """Check for the exact allowed Coroutine[object, None, T] shape."""
    if not isinstance(node, ast.Subscript) or not _is_coroutine_annotation(node):
        return False

    slice_node = node.slice
    if not isinstance(slice_node, ast.Tuple) or len(slice_node.elts) != _COROUTINE_ARG_COUNT:
        return False

    first_arg, second_arg, _third_arg = slice_node.elts
    return _is_object_name(first_arg) and isinstance(second_arg, ast.Constant) and second_arg.value is None


def _child_annotation_nodes(node: ast.expr) -> tuple[ast.expr, ...] | None:
    """Return child annotation nodes that should be checked recursively."""
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Tuple):
            return tuple(node.slice.elts)
        return (node.slice,)
    if isinstance(node, ast.Tuple):
        return tuple(node.elts)
    if isinstance(node, ast.BinOp):
        return (node.left, node.right)
    return None


def _annotation_has_banned_object(node: ast.expr) -> bool:
    """Check if a type annotation contains banned object usage."""
    if _is_allowed_coroutine_object(node):
        return False
    if _is_object_name(node):
        return True
    child_nodes = _child_annotation_nodes(node)
    return child_nodes is not None and any(_annotation_has_banned_object(child) for child in child_nodes)


def _is_typeis_guard(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if function return type is TypeIs[...] or TypeGuard[...]."""
    ret = func.returns
    if ret is None:
        return False
    if not isinstance(ret, ast.Subscript):
        return False
    if isinstance(ret.value, ast.Name):
        return ret.value.id in ("TypeIs", "TypeGuard")
    if isinstance(ret.value, ast.Attribute):
        return ret.value.attr in ("TypeIs", "TypeGuard")
    return False


def _is_variadic(arg: ast.arg, func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if arg is *args or **kwargs."""
    variadic_names: set[str] = set()
    if func.args.vararg is not None:
        variadic_names.add(func.args.vararg.arg)
    if func.args.kwarg is not None:
        variadic_names.add(func.args.kwarg.arg)
    return arg.arg in variadic_names


def _check_annotation_violation(
    path: Path,
    source_lines: list[str],
    annotation: ast.expr,
    violations: list[str],
    message: str,
) -> None:
    """Check a single annotation node for banned object usage."""
    if not _annotation_has_banned_object(annotation):
        return

    line_num = annotation.lineno
    source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

    if has_bare_ignore(source_line, CHECK_NAME):
        violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
        return
    if is_ignored(source_line, CHECK_NAME):
        return

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
                # Skip exact Coroutine[object, None, T] boundary annotations
                if _is_allowed_coroutine_object(arg.annotation):
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
