"""Shared utilities for custom linting scripts."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Final

# Pattern: # lint-ignore[check-name]: rationale text
_IGNORE_ENTRY_PATTERN = re.compile(r"#\s*lint-ignore\[([^\]]+)\](?::\s*(.*?))?(?=\s+#\s*lint-ignore\[|$)")
_FILE_IGNORE_ENTRY_PATTERN = re.compile(
    r"#\s*lint-ignore-file\[([^\]]+)\](?::\s*(.*?))?(?=\s+#\s*lint-ignore-file\[|$)"
)


def _iter_ignore_entries(line: str) -> list[tuple[str, str | None]]:
    """Return lint-ignore entries as ``(check_name, rationale)`` tuples.

    ``rationale`` is ``None`` when the ignore has no colon, an empty string when
    it has a colon but no text, and non-empty text when a rationale is present.
    """
    line_comment = comment_text(line)
    if line_comment is None:
        return []
    return [(match.group(1), match.group(2)) for match in _IGNORE_ENTRY_PATTERN.finditer(line_comment)]


def _iter_file_ignore_entries(line: str) -> list[tuple[str, str | None]]:
    """Return file-level lint-ignore entries as ``(check_name, rationale)`` tuples."""
    line_comment = comment_text(line)
    if line_comment is None:
        return []
    return [(match.group(1), match.group(2)) for match in _FILE_IGNORE_ENTRY_PATTERN.finditer(line_comment)]


def comment_text(line: str) -> str | None:
    """Return the Python comment token text for a source line, if any."""
    try:
        for token in tokenize.generate_tokens(io.StringIO(f"{line}\n").readline):
            if token.type == tokenize.COMMENT:
                return token.string
    except IndentationError, tokenize.TokenError:
        return None
    return None


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
    return any(name == check_name and bool(rationale) for name, rationale in _iter_ignore_entries(line))


def has_bare_ignore(line: str, check_name: str) -> bool:
    """Check if a source line has a lint-ignore WITHOUT rationale (error)."""
    return any(name == check_name and not rationale for name, rationale in _iter_ignore_entries(line))


def is_file_ignored(source_lines: list[str], check_name: str) -> bool:
    """Check if a file has a valid file-level lint-ignore for this check."""
    return any(
        name == check_name and bool(rationale)
        for line in source_lines
        for name, rationale in _iter_file_ignore_entries(line)
    )


def bare_file_ignore_line(source_lines: list[str], check_name: str) -> int | None:
    """Return the first bare file-level lint-ignore line for this check, if any."""
    for line_num, line in enumerate(source_lines, start=1):
        if any(name == check_name and not rationale for name, rationale in _iter_file_ignore_entries(line)):
            return line_num
    return None


def file_ignore_result(path: Path, source_lines: list[str], check_name: str) -> list[str] | None:
    """Return an early file-level ignore result for a lint check, if any."""
    line_num = bare_file_ignore_line(source_lines, check_name)
    if line_num is not None:
        return [report(path, line_num, check_name, "lint-ignore-file requires rationale after ':'")]
    if is_file_ignored(source_lines, check_name):
        return []
    return None


def read_source_lines(path: Path) -> list[str]:
    """Read a file's source lines. Returns empty list on read errors."""
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError, UnicodeDecodeError:
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
