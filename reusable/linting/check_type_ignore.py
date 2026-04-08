"""Check that type-ignore directives have an error code and rationale.

Usage: python -m reusable.linting.check_type_ignore [file1.py file2.py ...]
If no files given, scans current directory recursively.

Ignore with: # lint-ignore[type-ignore-rationale]: <rationale>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reusable.linting.lint_utils import (
    collect_files,
    has_bare_ignore,
    is_ignored,
    read_source_lines,
    report,
)

CHECK_NAME = "type-ignore-rationale"

# Matches `# type: ignore` with optional bracket  # lint-ignore[type-ignore-rationale]: pattern docs
# Handles: type:ignore, type: ignore, type:  ignore
_TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore")
_TYPE_IGNORE_WITH_CODE_RE = re.compile(r"#\s*type:\s*ignore\[([^\]]+)\]")

# After the type:ignore[code] part, check for a rationale comment
# Must be a `# ...` comment that is NOT a `# lint-ignore[...]`
_RATIONALE_RE = re.compile(r"#\s*type:\s*ignore\[[^\]]+\]\s+#\s*(?!lint-ignore\[)")


def check_file(path: Path) -> list[str]:
    """Check a single file for type:ignore directives missing rationale."""
    source_lines = read_source_lines(path)
    if not source_lines:
        return []

    violations: list[str] = []

    for line_num, line in enumerate(source_lines, start=1):
        if not _TYPE_IGNORE_RE.search(line):
            continue

        if has_bare_ignore(line, CHECK_NAME):
            violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
            continue

        if is_ignored(line, CHECK_NAME):
            continue

        # Check for bare type:ignore (no error code)
        if not _TYPE_IGNORE_WITH_CODE_RE.search(line):
            violations.append(
                report(path, line_num, CHECK_NAME, "bare 'type: ignore' must specify error code, e.g. [assignment]")
            )
            continue

        # Has error code — check for rationale comment after it
        if not _RATIONALE_RE.search(line):
            violations.append(report(path, line_num, CHECK_NAME, "type: ignore[code] must include rationale comment"))

    return violations


if __name__ == "__main__":
    files = collect_files(sys.argv[1:])
    all_violations: list[str] = []
    for f in files:
        all_violations.extend(check_file(f))
    for v in all_violations:
        print(v)
    sys.exit(1 if all_violations else 0)
