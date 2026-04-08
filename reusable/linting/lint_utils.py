"""Shared utilities for custom linting scripts."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

# Pattern: # lint-ignore[check-name]: rationale text
_IGNORE_PATTERN = re.compile(r"#\s*lint-ignore\[([^\]]+)\]\s*:\s*(.+?)(?=\s+#\s*lint-ignore\[|$)")
_IGNORE_NO_RATIONALE = re.compile(r"#\s*lint-ignore\[([^\]]+)\]\s*:?\s*$")


_EXCLUDED_DIRS: Final = frozenset(
    {".venv", "venv", ".git", "__pycache__", "node_modules", ".tox", ".mypy_cache", "fixtures"}
)


def _is_excluded(path: Path) -> bool:
    """Check if a path is under an excluded directory."""
    return bool(_EXCLUDED_DIRS & set(path.parts))


def collect_files(args: list[str]) -> list[Path]:
    """Collect Python files from CLI args or scan current directory."""
    if args:
        return [Path(a) for a in args if a.endswith(".py")]
    return sorted(p for p in Path(".").rglob("*.py") if not _is_excluded(p))


def is_ignored(line: str, check_name: str) -> bool:
    """Check if a source line has a valid lint-ignore comment for this check."""
    return any(match.group(1) == check_name for match in _IGNORE_PATTERN.finditer(line))


def has_bare_ignore(line: str, check_name: str) -> bool:
    """Check if a source line has a lint-ignore WITHOUT rationale (error)."""
    if _IGNORE_PATTERN.search(line):
        return False  # Has rationale — not bare
    match = _IGNORE_NO_RATIONALE.search(line)
    return bool(match and match.group(1) == check_name)


def read_source_lines(path: Path) -> list[str]:
    """Read a file's source lines. Returns empty list on read errors."""
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def report(path: Path, line: int, check_name: str, message: str) -> str:
    """Format a violation report line."""
    return f"{path}:{line}: [{check_name}] {message}"


def is_final_annotation(annotation: ast.expr | None) -> bool:
    """Check if annotation is Final or Final[...].

    Handles both ``Final`` / ``typing.Final`` name forms and
    ``Final[T]`` / ``typing.Final[T]`` subscript forms.
    """
    if annotation is None:
        return False
    # Final (bare name)
    if isinstance(annotation, ast.Name) and annotation.id == "Final":
        return True
    # typing.Final (attribute access)
    if isinstance(annotation, ast.Attribute) and annotation.attr == "Final":
        return True
    # Final[T] or typing.Final[T]
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        if isinstance(value, ast.Name) and value.id == "Final":
            return True
        if isinstance(value, ast.Attribute) and value.attr == "Final":
            return True
    return False
