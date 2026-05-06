"""Check for ignored Result-returning function calls in expression statements.

Current scope is intentionally narrow: it flags bare expression-statement calls
to Result-returning functions defined in the same file and a few simple local
import forms that resolve to nearby project files.

Usage: python -m shared.linting.check_ignored_results [file1.py file2.py ...]
Ignore with: # lint-ignore[ignored-result]: <rationale>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from shared.linting.lint_utils import (
    collect_files,
    file_ignore_result,
    has_bare_ignore,
    is_ignored,
    read_source_lines,
    report,
)

CHECK_NAME = "ignored-result"

type ResultFunctionCache = dict[Path, set[str]]
type ModuleCallMap = dict[tuple[str, ...], set[str]]


def _result_type_info(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Collect local names and module aliases that refer to rusty_results.Result."""
    type_names: set[str] = set()
    module_names = {"rusty_results"}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "rusty_results":
            for alias in node.names:
                if alias.name == "Result":
                    type_names.add(alias.asname or alias.name)
            continue
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            if alias.name == "rusty_results":
                module_names.add(alias.asname or alias.name)
    return type_names, module_names


def _is_result_annotation_base(node: ast.expr, result_type_names: set[str], result_module_names: set[str]) -> bool:
    """Return whether an annotation base refers to rusty_results.Result."""
    if isinstance(node, ast.Name):
        return node.id in result_type_names
    if not isinstance(node, ast.Attribute) or node.attr != "Result":
        return False
    return isinstance(node.value, ast.Name) and node.value.id in result_module_names


def _returns_result(annotation: ast.expr | None, result_type_names: set[str], result_module_names: set[str]) -> bool:
    """Return whether an annotation is Result, Result[...], or rusty_results.Result[...]."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Subscript):
        return _is_result_annotation_base(annotation.value, result_type_names, result_module_names)
    return _is_result_annotation_base(annotation, result_type_names, result_module_names)


def _result_function_names(tree: ast.Module, result_type_names: set[str], result_module_names: set[str]) -> set[str]:
    """Collect module-level function names annotated to return Result."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _returns_result(
            node.returns,
            result_type_names,
            result_module_names,
        ):
            names.add(node.name)
    return names


def _resolve_relative_module_path(current_path: Path, module_name: str | None, level: int) -> Path | None:
    """Resolve a relative import path from the current file location."""
    base_dir = current_path.parent
    for _ in range(level - 1):
        base_dir = base_dir.parent
    if module_name is None:
        package_init = base_dir / "__init__.py"
        return package_init if package_init.is_file() else None

    parts = module_name.split(".")
    module_file = base_dir.joinpath(*parts).with_suffix(".py")
    if module_file.is_file():
        return module_file
    package_init = base_dir.joinpath(*parts, "__init__.py")
    if package_init.is_file():
        return package_init
    return None


def _resolve_absolute_module_path(current_path: Path, module_name: str) -> Path | None:
    """Resolve a narrow absolute local module path from the current file location."""
    parts = module_name.split(".")
    parent_dir = current_path.parent
    if (parent_dir / "__init__.py").is_file():
        base_dir = parent_dir
        while (base_dir / "__init__.py").is_file():
            base_dir = base_dir.parent
        candidate_dirs = (base_dir, base_dir.parent) if base_dir.name in {"src", "tests"} else (base_dir,)
    else:
        candidate_dirs = tuple(
            dict.fromkeys(
                (
                    *current_path.parents,
                    *(parent / "src" for parent in current_path.parents),
                )
            )
        )

    for base_dir in candidate_dirs:
        module_file = base_dir.joinpath(*parts).with_suffix(".py")
        if module_file.is_file():
            return module_file

        package_init = base_dir.joinpath(*parts, "__init__.py")
        if package_init.is_file():
            return package_init

    return None


def _resolve_module_path(current_path: Path, module_name: str | None, level: int = 0) -> Path | None:
    """Resolve a narrow local module path for absolute or relative imports."""
    if level > 0:
        return _resolve_relative_module_path(current_path, module_name, level)
    if module_name is None:
        return None
    return _resolve_absolute_module_path(current_path, module_name)


def _parse_result_functions(
    path: Path,
    cache: ResultFunctionCache,
    visiting: set[Path] | None = None,
) -> set[str]:
    """Parse a local module and collect its Result-returning functions."""
    cached = cache.get(path)
    if cached is not None:
        return cached

    if visiting is None:
        visiting = set()
    if path in visiting:
        return set()
    visiting.add(path)

    source_lines = read_source_lines(path)
    if not source_lines:
        cache[path] = set()
        visiting.remove(path)
        return cache[path]

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        cache[path] = set()
        visiting.remove(path)
        return cache[path]

    result_type_names, result_module_names = _result_type_info(tree)
    result_functions = _result_function_names(tree, result_type_names, result_module_names)

    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        module_path = _resolve_module_path(path, node.module, node.level)
        if module_path is None:
            continue
        imported_result_functions = _parse_result_functions(module_path, cache, visiting)
        for alias in node.names:
            if alias.name in imported_result_functions:
                result_functions.add(alias.asname or alias.name)

    cache[path] = result_functions
    visiting.remove(path)
    return cache[path]


def _imported_result_symbols(
    path: Path,
    tree: ast.Module,
    local_result_functions: set[str],
) -> tuple[set[str], ModuleCallMap]:
    """Collect direct call names and module aliases for narrow local imports."""
    direct_calls = set(local_result_functions)
    module_calls: ModuleCallMap = {}
    result_function_cache: ResultFunctionCache = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module_path = _resolve_module_path(path, node.module, node.level)
            if module_path is None:
                continue
            result_functions = _parse_result_functions(module_path, result_function_cache)
            for alias in node.names:
                if alias.name in result_functions:
                    direct_calls.add(alias.asname or alias.name)

        if isinstance(node, ast.Import):
            for alias in node.names:
                module_path = _resolve_module_path(path, alias.name)
                if module_path is None:
                    continue
                result_functions = _parse_result_functions(module_path, result_function_cache)
                if result_functions:
                    local_name = alias.asname or alias.name
                    module_key = (local_name,) if alias.asname is not None else tuple(alias.name.split("."))
                    module_calls[module_key] = result_functions

    return direct_calls, module_calls


def _attribute_chain(expr: ast.expr) -> tuple[str, ...] | None:
    """Return the dotted attribute chain for an expression, if any."""
    if isinstance(expr, ast.Name):
        return (expr.id,)
    if not isinstance(expr, ast.Attribute):
        return None
    parent_chain = _attribute_chain(expr.value)
    if parent_chain is None:
        return None
    return (*parent_chain, expr.attr)


def _called_result_function_name(
    expr: ast.expr,
    direct_calls: set[str],
    module_calls: ModuleCallMap,
) -> str | None:
    """Return the called function name when expr ignores a known Result call."""
    if isinstance(expr, ast.Await):
        expr = expr.value
    if not isinstance(expr, ast.Call):
        return None
    if isinstance(expr.func, ast.Name) and expr.func.id in direct_calls:
        return expr.func.id
    if isinstance(expr.func, ast.Attribute):
        owner_chain = _attribute_chain(expr.func.value)
        if owner_chain is not None and owner_chain in module_calls and expr.func.attr in module_calls[owner_chain]:
            return ".".join((*owner_chain, expr.func.attr))
    return None


def check_file(path: Path) -> list[str]:
    """Check a single file for ignored Result-returning calls."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    early_result = file_ignore_result(path, source_lines, CHECK_NAME)
    if early_result is not None:
        return early_result

    try:
        tree = ast.parse("\n".join(source_lines), filename=str(path))
    except SyntaxError:
        return []

    result_type_names, result_module_names = _result_type_info(tree)
    result_functions = _result_function_names(tree, result_type_names, result_module_names)
    direct_calls, module_calls = _imported_result_symbols(path, tree, result_functions)
    if not direct_calls and not module_calls:
        return []

    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue

        function_name = _called_result_function_name(node.value, direct_calls, module_calls)
        if function_name is None:
            continue

        line_num = node.lineno
        source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

        if has_bare_ignore(source_line, CHECK_NAME):
            violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
            continue
        if is_ignored(source_line, CHECK_NAME):
            continue

        violations.append(report(path, line_num, CHECK_NAME, f"ignored Result return from '{function_name}'"))

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for file_path in files:
        all_violations.extend(check_file(file_path))
    for violation in all_violations:
        print(violation)
    sys.exit(1 if all_violations else 0)
