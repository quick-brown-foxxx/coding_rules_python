# Coding Rules Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten Python coding standards with 8 new rules, fix 5 inconsistencies, add automated enforcement via 3 custom linting scripts, and update ruff/basedpyright configs.

**Architecture:** Two parallel tracks. Track A edits documentation files (rules, skills, templates). Track B creates linting scripts in `reusable/linting/` with tests in `reusable_tests/test_linting/`. Both tracks are independent.

**Tech Stack:** Python 3.14 stdlib (`ast`, `sys`, `pathlib`), pytest, ruff, basedpyright, poethepoet

---

## Track A — Documentation Updates

### Task A1: Fix existing inconsistencies

**Files:**
- Modify: `notes/other-patterns.md`
- Modify: `skills/testing-python/SKILL.md`
- Modify: `skills/writing-python-code/SKILL.md`
- Modify: `skills/building-qt-apps/SKILL.md`

- [ ] **Step 1: Fix `dict[str, object]` in `notes/other-patterns.md`**

In `notes/other-patterns.md`, replace all 3 instances of `dict[str, object]` with a proper config value union type.

Lines 36-37: change the function signature and variable:
```python
# Before:
def load_configs(paths: list[Path]) -> Result[dict[str, object], str]:
    merged: dict[str, object] = {}

# After:
# Use a type alias for config values
type ConfigValue = str | int | float | bool | list[str]

def load_configs(paths: list[Path]) -> Result[dict[str, ConfigValue], str]:
    merged: dict[str, ConfigValue] = {}
```

Line 51: change the validate function:
```python
# Before:
def validate_config(config: dict[str, object], schema_path: Path) -> Result[None, str]:

# After:
def validate_config(config: dict[str, ConfigValue], schema_path: Path) -> Result[None, str]:
```

- [ ] **Step 2: Fix `dict[str, object]` in `skills/testing-python/SKILL.md`**

Line 381, in the MockAPIHandler class:
```python
# Before:
    profiles: dict[str, dict[str, object]] = {}

# After:
    profiles: dict[str, dict[str, str | int | bool]] = {}
```

- [ ] **Step 3: Fix `dict[str, object]` in `skills/writing-python-code/SKILL.md`**

Line 149, in the ValidResponse TypedDict:
```python
# Before:
class ValidResponse(TypedDict):
    status: Required[str]
    data: Required[dict[str, object]]

# After:
class ValidResponse(TypedDict):
    status: Required[str]
    data: Required[dict[str, str | int | bool | list[str]]]
```

- [ ] **Step 4: Fix `Signal(object)` docs in `skills/building-qt-apps/SKILL.md`**

Line 208, change:
```markdown
- Use typed signals: `Signal(str)`, `Signal(float)`, `Signal(object)`
```
to:
```markdown
- Use typed signals: `Signal(str)`, `Signal(float)`. Use `Signal(object)` only when PySide6 lacks generic signal support — add `# PySide6 limitation: no generic signals` comment
```

- [ ] **Step 5: Commit**

```bash
git add notes/other-patterns.md skills/testing-python/SKILL.md skills/writing-python-code/SKILL.md skills/building-qt-apps/SKILL.md
git commit -m "fix: replace dict[str, object] in examples, clarify Signal(object)"
```

### Task A2: Add new rules to `coding_rules.md`

**Files:**
- Modify: `rules/coding_rules.md`

This task adds 6 new subsections to `coding_rules.md`. All additions go into existing sections.

- [ ] **Step 1: Add §1.6 Immutability after the Constants section (after line 108)**

Insert after the Constants section:

````markdown
### 1.6 Immutability

Prefer immutable data by default. Mutable structures require justification.

- `@dataclass(frozen=True, slots=True)` is the default. Omit `frozen` only for builder patterns or explicit accumulation with a comment.
- Return `tuple` over `list` for fixed collections. Use `Sequence` in parameters that don't mutate.
- `frozenset` over `set` when mutation isn't needed.

```python
@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    version: str
    active: bool = True
```
````

- [ ] **Step 2: Add §1.7 Domain Identifiers (NewType) after §1.6**

````markdown
### 1.7 Domain Identifiers

Use `NewType` for domain IDs and typed strings that must not be interchangeable. Use `Path` for filesystem paths, never raw `str`.

```python
from typing import NewType

ProfileId = NewType("ProfileId", str)
UserId = NewType("UserId", str)

def delete_profile(profile_id: ProfileId) -> Result[None, str]: ...
# delete_profile(user_id)  # basedpyright error — caught at check time
```
````

- [ ] **Step 3: Add §1.8 Enum vs Literal vs Union after §1.7**

```markdown
### 1.8 Enum vs Literal vs Union

| Use case                                         | Tool                                       |
| ------------------------------------------------ | ------------------------------------------ |
| Small fixed string set in function params         | `Literal["json", "yaml"]`                  |
| Value set with behavior, iteration, or in models | `StrEnum`                                  |
| Structurally different variants                   | Union type: `type Outcome = Success \| Failure` |
| C/binary protocol interop                         | `IntEnum`                                  |
```

- [ ] **Step 4: Add function signature rules to §3 Code Style (after §3.2 Naming)**

Insert as new §3.3:

```markdown
### 3.3 Function Signatures

- **Maximum 5 parameters.** Beyond that, group into a config `dataclass` or `msgspec.Struct`. Enforced by ruff `PLR0913`.
- **No boolean flag parameters** that switch behavior. Use two named functions or an enum parameter. Enforced by ruff `FBT001`/`FBT002`.
- Functions in the same module with similar purposes must have consistent parameter ordering.
```

- [ ] **Step 5: Add module-level state ban and circular imports to §6 Architecture**

After §6.3 Scale-Appropriate (before §6.4 Graceful Shutdown), insert:

```markdown
### 6.4 Module-Level State

Module-level mutable state is banned. All module globals must be `Final`. Registries, caches, and singletons belong in explicitly constructed objects passed via dependency injection. Exceptions: `logging.getLogger()` and `Final` constants.

### 6.5 Circular Imports

Circular imports are architectural bugs — not something to work around with `TYPE_CHECKING`. If two modules import each other, invert the dependency: extract a `Protocol`, move shared types to a common module, or restructure layers. `TYPE_CHECKING` is only for forward references within the same layer. Enforce layer boundaries with ruff `banned-api` where practical.
```

Note: renumber existing §6.4 Graceful Shutdown to §6.6.

- [ ] **Step 6: Commit**

```bash
git add rules/coding_rules.md
git commit -m "feat(rules): add immutability, NewType, enum discipline, signature limits, module state ban, circular imports"
```

### Task A3: Rewrite `object` guidance in rules and skill

**Files:**
- Modify: `rules/coding_rules.md`
- Modify: `skills/writing-python-code/SKILL.md`

- [ ] **Step 1: Update banned patterns table in `rules/coding_rules.md`**

Replace the table at lines 19-25:

```markdown
### 1.2 Banned Patterns

| Banned                             | Use Instead                                            |
| ---------------------------------- | ------------------------------------------------------ |
| `Any`                              | Banned entirely. No replacement — define the actual type |
| `object` (unrestricted)            | Restricted to boundary positions only (see §1.3)       |
| `typing.cast()`                    | `isinstance`, `TypeIs`, pattern matching               |
| `# type: ignore` without rationale | `# type: ignore[specific-code]  # rationale: <reason>` |
| Raw `dict` in business logic       | `msgspec.Struct`, `dataclass`, or `TypedDict`          |
| Implicit return types              | Explicit annotation on every function                  |
```

Then add a new §1.3 (renumber existing §1.3 to §1.4, etc.):

```markdown
### 1.3 Restricted `object`

`object` is the top type but offers no useful operations without narrowing. It is allowed **only** in boundary/guard positions:

| Allowed use                        | Example                                      |
| ---------------------------------- | -------------------------------------------- |
| `TypeIs`/`TypeGuard` parameters    | `def is_valid(obj: object) -> TypeIs[Config]` |
| Variadic signal/handler args       | `*_args: object`                              |
| Coroutine type params              | `Coroutine[object, None, T]`                  |
| PySide6 `Signal(object)`           | PySide6 limitation — no generic signals       |

Everywhere else, replace `object` with the actual type: `Protocol` for duck typing, `TypeVar` for generics, explicit union for known variants, `msgspec.Struct`/`TypedDict` for dict shapes.
```

- [ ] **Step 2: Update banned patterns table in `skills/writing-python-code/SKILL.md`**

Replace the table at lines 42-49 with the same updated table:

```markdown
### Banned Patterns

| Banned | Use Instead |
|--------|-------------|
| `Any` | Banned entirely — define the actual type |
| `object` (unrestricted) | Restricted to boundary positions only (see below) |
| `typing.cast()` | `isinstance`, `TypeIs`, pattern matching |
| `# type: ignore` without rationale | `# type: ignore[specific-code]  # rationale: <reason>` |
| Raw `dict` in business logic | `msgspec.Struct`, `dataclass`, or `TypedDict` |
| Implicit return types | Explicit annotation on every function |

**`object` is allowed only in:** TypeIs/TypeGuard params, `*args: object`, `Coroutine[object, None, T]`, PySide6 `Signal(object)`. Everywhere else, use `Protocol`, `TypeVar`, union types, or typed structures.
```

- [ ] **Step 3: Commit**

```bash
git add rules/coding_rules.md skills/writing-python-code/SKILL.md
git commit -m "feat(rules): restrict object to boundary positions, split from Any ban"
```

### Task A4: Add DI composition root to `building-multi-ui-apps/SKILL.md`

**Files:**
- Modify: `skills/building-multi-ui-apps/SKILL.md`
- Modify: `skills/building-qt-apps/SKILL.md`

- [ ] **Step 1: Add DI section to `building-multi-ui-apps/SKILL.md`**

Add before the "Other Presentation Layers" section (before line 133):

````markdown
---

## Dependency Injection — Composition Root

Pass dependencies via constructor parameters. Wire everything in a single composition root function. No DI libraries — they break basedpyright strict or add unnecessary indirection.

### Pattern

```python
# app/bootstrap.py
def create_domain(config: AppConfig) -> SessionManager:
    """Composition root — the ONLY place dependencies are wired."""
    db = DatabaseWrapper(config.db_path)
    api = ApiClientWrapper(config.api_url, config.api_key)
    auth = AuthService(api_client=api)
    sync = SyncService(db=db, api_client=api)
    return SessionManager(auth=auth, sync=sync)

# GUI entry point
def main_gui() -> None:
    config = load_config()
    session = create_domain(config)
    window = MainWindow(session=session)
    ...

# CLI entry point
def main_cli() -> None:
    config = load_config()
    session = create_domain(config)
    cli_app = build_typer_app(session=session)
    cli_app()
```

### Rules

- **Domain classes never instantiate their own infrastructure.** Dependencies come through the constructor.
- **One composition root per app.** This is the single place to understand the object graph.
- **Protocol-typed interfaces** for dependencies that may have test doubles.
- **Testing:** construct with fakes directly — no container setup needed:

```python
def test_sync_handles_conflict() -> None:
    db = FakeDatabaseWrapper()
    api = FakeApiClient(responses=[CONFLICT_RESPONSE])
    sync = SyncService(db=db, api_client=api)
    result = sync.pull_changes()
    assert result.is_err
```
````

- [ ] **Step 2: Add cross-reference in `building-qt-apps/SKILL.md`**

After the "Architecture: Manager → Service → Wrapper" section heading (around line 12), add a note:

```markdown
For dependency wiring patterns (composition root), see `building-multi-ui-apps` skill.
```

- [ ] **Step 3: Commit**

```bash
git add skills/building-multi-ui-apps/SKILL.md skills/building-qt-apps/SKILL.md
git commit -m "feat(skills): add DI composition root pattern to multi-ui skill"
```

### Task A5: Update `writing-python-code/SKILL.md` — immutability + TYPE_CHECKING note

**Files:**
- Modify: `skills/writing-python-code/SKILL.md`

- [ ] **Step 1: Update dataclass example to show `frozen=True`**

Line ~72, change the domain objects example:

```python
# Before:
@dataclass(slots=True)
class Profile:
    name: str
    version: str
    active: bool = True

# After:
@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    version: str
    active: bool = True
```

- [ ] **Step 2: Add circular imports note to TYPE_CHECKING section**

At the end of the TYPE_CHECKING Guard section (around line 213), add:

```markdown
> **Note:** `TYPE_CHECKING` is for forward references within the same layer. If two modules import each other, that's a circular dependency — fix the architecture (extract a Protocol, move types to a common module), don't hide the cycle with `TYPE_CHECKING`.
```

- [ ] **Step 3: Commit**

```bash
git add skills/writing-python-code/SKILL.md
git commit -m "feat(skills): add frozen=True default, circular import note"
```

### Task A6: Update short rules and templates

**Files:**
- Modify: `rules/coding_rules_short.md`
- Modify: `templates/pyproject.toml`

- [ ] **Step 1: Update `coding_rules_short.md`**

Replace the Type Safety section:

```markdown
## Type Safety

- basedpyright strict mode, `reportAny=error`, `reportImportCycles=error`
- Type annotations on all functions
- No `Any`, no `typing.cast()`, no blanket `# type: ignore`
- `object` restricted to boundary positions (TypeIs guards, signal handlers, coroutine params)
- `msgspec.Struct` for external data (JSON, configs, APIs), `dataclass(frozen=True)` for domain objects
- `NewType` for domain identifiers (ProfileId, UserId) — prevent mixing
- Immutable by default: `frozen=True`, `tuple` over `list`, `Sequence` in params
- Max 5 function parameters; no boolean flag params
```

- [ ] **Step 2: Update `templates/pyproject.toml` — add ruff PLR/FBT rules**

Add `"PLR"` and `"FBT"` to the `extend-select` list in `[tool.ruff.lint]`:

```toml
extend-select = [
    "E", "F", "W",   # pycodestyle + pyflakes
    "I",              # isort
    "N",              # naming
    "UP",             # pyupgrade
    "ASYNC",          # async best practices
    "S",              # bandit security
    "B",              # bugbear
    "A",              # builtins
    "C4",             # comprehensions
    "SIM",            # simplify
    "PT",             # pytest style
    "PERF",           # performance
    "PLR",            # pylint refactor (max args, complexity)
    "FBT",            # flake8-boolean-trap (no bool params)
    "RUF",            # ruff-specific
]
```

Add after the `[tool.ruff.lint.per-file-ignores]` section:

```toml
[tool.ruff.lint.pylint]
max-args = 5
```

Add `reportImportCycles = "error"` to the basedpyright config:

```toml
[tool.basedpyright]
# ... existing settings ...
reportImportCycles = "error"
```

Add `FBT001` to test file ignores:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "PT018", "FBT001"]
```

- [ ] **Step 3: Update `templates/pyproject.toml` — add poe tasks for custom linting**

Add individual lint tasks and update lint_full. After the existing `[tool.poe.tasks]` section:

```toml
[tool.poe.tasks]
test = "pytest"
app = "python -m TODO_PACKAGE_NAME"
lint_objects = "python reusable/linting/check_object_annotations.py"
lint_frozen = "python reusable/linting/check_frozen_dataclasses.py"
lint_mutables = "python reusable/linting/check_module_mutables.py"

[tool.poe.tasks.lint_custom]
sequence = ["lint_objects", "lint_frozen", "lint_mutables"]

[tool.poe.tasks.lint_full]
shell = "basedpyright . && ruff check --fix . && ruff format . && poe lint_custom"
```

- [ ] **Step 4: Update `templates/pre-commit-config.yaml` — add custom linting hooks**

Add after the basedpyright hook:

```yaml
      - id: check-object-annotations
        name: check-object-annotations
        entry: uv run python reusable/linting/check_object_annotations.py
        language: system
        types: [python]

      - id: check-frozen-dataclasses
        name: check-frozen-dataclasses
        entry: uv run python reusable/linting/check_frozen_dataclasses.py
        language: system
        types: [python]

      - id: check-module-mutables
        name: check-module-mutables
        entry: uv run python reusable/linting/check_module_mutables.py
        language: system
        types: [python]
```

- [ ] **Step 5: Commit**

```bash
git add rules/coding_rules_short.md templates/pyproject.toml templates/pre-commit-config.yaml
git commit -m "feat(templates): add PLR/FBT ruff rules, reportImportCycles, custom lint poe tasks"
```

---

## Track B — Custom Linting Scripts

### Task B1: Create shared linting utilities module

**Files:**
- Create: `reusable/linting/__init__.py`
- Create: `reusable/linting/lint_utils.py`

- [ ] **Step 1: Create `reusable/linting/__init__.py`**

```python
"""Custom linting scripts for Python coding standards.

AST-based checks that complement ruff and basedpyright.
Pure stdlib — no external dependencies.
"""
```

- [ ] **Step 2: Create `reusable/linting/lint_utils.py`**

This module contains shared utilities used by all three linting scripts.

```python
"""Shared utilities for custom linting scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Pattern: # lint-ignore[check-name]: rationale text
_IGNORE_PATTERN = re.compile(r"#\s*lint-ignore\[([^\]]+)\]\s*:\s*(.+)")
_IGNORE_NO_RATIONALE = re.compile(r"#\s*lint-ignore\[([^\]]+)\]\s*:?\s*$")


def collect_files(args: list[str]) -> list[Path]:
    """Collect Python files from CLI args or scan current directory."""
    if args:
        return [Path(a) for a in args if a.endswith(".py")]
    return sorted(Path(".").rglob("*.py"))


def is_ignored(line: str, check_name: str) -> bool:
    """Check if a source line has a valid lint-ignore comment for this check."""
    match = _IGNORE_PATTERN.search(line)
    if match and match.group(1) == check_name:
        return True
    return False


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


def main_runner(check_fn: object, args: list[str] | None = None) -> int:
    """Common main entry point for linting scripts.

    Args:
        check_fn: A callable(Path) -> list[str] that returns violation messages.
        args: CLI args (defaults to sys.argv[1:]).

    Returns:
        0 if clean, 1 if violations found.
    """
    if args is None:
        args = sys.argv[1:]
    files = collect_files(args)
    violations: list[str] = []
    for path in files:
        # check_fn is typed loosely here because this is a utility runner;
        # each script passes its own typed function
        results = check_fn(path)  # type: ignore[operator]  # rationale: generic runner, callers pass correct callable
        violations.extend(results)
    for v in violations:
        print(v)
    return 1 if violations else 0
```

- [ ] **Step 3: Commit**

```bash
git add reusable/linting/__init__.py reusable/linting/lint_utils.py
git commit -m "feat(linting): add shared lint utilities module"
```

### Task B2: Create `check_frozen_dataclasses.py` (simplest script)

**Files:**
- Create: `reusable/linting/check_frozen_dataclasses.py`
- Create: `reusable_tests/fixtures/linting/frozen_pass.py`
- Create: `reusable_tests/fixtures/linting/frozen_fail.py`
- Create: `reusable_tests/fixtures/linting/frozen_ignore.py`
- Create: `reusable_tests/fixtures/linting/frozen_bare_ignore.py`
- Create: `reusable_tests/test_linting/__init__.py`
- Create: `reusable_tests/test_linting/test_check_frozen_dataclasses.py`

- [ ] **Step 1: Create test fixtures**

Create `reusable_tests/fixtures/linting/frozen_pass.py`:
```python
"""Fixture: all dataclasses have frozen=True — should PASS."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleProfile:
    name: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class DetailedProfile:
    name: str
    version: str
    active: bool = True


# Not a dataclass — should be ignored
class RegularClass:
    pass
```

Create `reusable_tests/fixtures/linting/frozen_fail.py`:
```python
"""Fixture: dataclasses missing frozen=True — should FAIL."""
from dataclasses import dataclass


@dataclass
class UnfrozenSimple:
    name: str


@dataclass(slots=True)
class UnfrozenWithSlots:
    name: str
    version: str


@dataclass(frozen=False)
class ExplicitlyUnfrozen:
    name: str
```

Create `reusable_tests/fixtures/linting/frozen_ignore.py`:
```python
"""Fixture: unfrozen dataclass with valid ignore — should PASS."""
from dataclasses import dataclass


@dataclass(slots=True)  # lint-ignore[unfrozen-dataclass]: builder pattern needs mutation
class Builder:
    name: str
    items: list[str]
```

Create `reusable_tests/fixtures/linting/frozen_bare_ignore.py`:
```python
"""Fixture: unfrozen dataclass with bare ignore (no rationale) — should FAIL."""
from dataclasses import dataclass


@dataclass  # lint-ignore[unfrozen-dataclass]
class NoRationale:
    name: str
```

- [ ] **Step 2: Write tests**

Create `reusable_tests/test_linting/__init__.py`:
```python
"""Tests for custom linting scripts."""
```

Create `reusable_tests/test_linting/test_check_frozen_dataclasses.py`:
```python
"""Tests for check_frozen_dataclasses linting script."""
from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path("reusable/linting/check_frozen_dataclasses.py")
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(SCRIPT), str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestFrozenDataclasses:
    def test_pass_frozen_dataclasses(self) -> None:
        result = _run("frozen_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_unfrozen_dataclasses(self) -> None:
        result = _run("frozen_fail.py")
        assert result.returncode == 1
        assert "[unfrozen-dataclass]" in result.stdout
        # Should catch all 3 unfrozen classes
        assert result.stdout.count("[unfrozen-dataclass]") == 3

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("frozen_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("frozen_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[unfrozen-dataclass]" in result.stdout
```

- [ ] **Step 3: Run tests — verify they fail (script not yet created)**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_frozen_dataclasses.py -v
```

Expected: FAIL (script doesn't exist yet)

- [ ] **Step 4: Implement `check_frozen_dataclasses.py`**

Create `reusable/linting/check_frozen_dataclasses.py`:
```python
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
                violations.append(
                    report(path, line_num, CHECK_NAME, f"dataclass '{node.name}' missing frozen=True")
                )
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
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_frozen_dataclasses.py -v
```

Expected: PASS

- [ ] **Step 6: Run linter on the script itself**

```bash
cd /var/home/user1/Projects/coding_rules_python && uv run ruff check reusable/linting/ && uv run basedpyright reusable/linting/
```

Expected: clean (or fix any issues)

- [ ] **Step 7: Commit**

```bash
git add reusable/linting/check_frozen_dataclasses.py reusable_tests/test_linting/ reusable_tests/fixtures/linting/
git commit -m "feat(linting): add check_frozen_dataclasses script with tests"
```

### Task B3: Create `check_object_annotations.py`

**Files:**
- Create: `reusable/linting/check_object_annotations.py`
- Create: `reusable_tests/fixtures/linting/object_pass.py`
- Create: `reusable_tests/fixtures/linting/object_fail.py`
- Create: `reusable_tests/fixtures/linting/object_ignore.py`
- Create: `reusable_tests/fixtures/linting/object_bare_ignore.py`
- Create: `reusable_tests/test_linting/test_check_object_annotations.py`

- [ ] **Step 1: Create test fixtures**

Create `reusable_tests/fixtures/linting/object_pass.py`:
```python
"""Fixture: valid object uses — should PASS."""
from __future__ import annotations

from collections.abc import Coroutine
from typing import TypeIs


class MyConfig:
    name: str


# TypeIs guard — allowed
def is_config(obj: object) -> TypeIs[MyConfig]:
    return isinstance(obj, MyConfig)


# Variadic args — allowed
def signal_handler(*_args: object) -> None:
    pass


# Coroutine type param — allowed
async def run_coro(coro: Coroutine[object, None, str]) -> str:
    return await coro


# Normal typed code — no object at all
def process(name: str, count: int) -> str:
    return f"{name}: {count}"
```

Create `reusable_tests/fixtures/linting/object_fail.py`:
```python
"""Fixture: banned object uses — should FAIL."""
from __future__ import annotations

from typing import Required, TypedDict


# dict[str, object] — banned
def load_data(path: str) -> dict[str, object]:
    return {}


# list[object] — banned
def get_items() -> list[object]:
    return []


# Bare object param (not TypeIs) — banned
def process(data: object) -> str:
    return str(data)


# TypedDict with dict[str, object] — banned
class Response(TypedDict):
    data: Required[dict[str, object]]
```

Create `reusable_tests/fixtures/linting/object_ignore.py`:
```python
"""Fixture: banned object use with valid ignore — should PASS."""
from __future__ import annotations


def log_value(label: str, value: object) -> None:  # lint-ignore[restricted-object]: logging utility accepts any printable
    print(f"{label}: {value}")
```

Create `reusable_tests/fixtures/linting/object_bare_ignore.py`:
```python
"""Fixture: banned object use with bare ignore — should FAIL."""
from __future__ import annotations


def process(data: object) -> str:  # lint-ignore[restricted-object]
    return str(data)
```

- [ ] **Step 2: Write tests**

Create `reusable_tests/test_linting/test_check_object_annotations.py`:
```python
"""Tests for check_object_annotations linting script."""
from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path("reusable/linting/check_object_annotations.py")
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(SCRIPT), str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestObjectAnnotations:
    def test_pass_valid_object_uses(self) -> None:
        result = _run("object_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_banned_object_uses(self) -> None:
        result = _run("object_fail.py")
        assert result.returncode == 1
        assert "[restricted-object]" in result.stdout
        # Should catch: dict[str, object], list[object], bare object param, TypedDict field
        assert result.stdout.count("[restricted-object]") >= 3

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("object_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("object_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[restricted-object]" in result.stdout
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_object_annotations.py -v
```

Expected: FAIL

- [ ] **Step 4: Implement `check_object_annotations.py`**

Create `reusable/linting/check_object_annotations.py`:
```python
"""Check that `object` is only used in boundary/guard positions.

Flags: dict[str, object], list[object], Sequence[object], tuple[object, ...],
and bare `object` function params (except TypeIs/TypeGuard guards, *args, **kwargs).

Usage: python check_object_annotations.py [file1.py file2.py ...]
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


def _is_typeis_guard(func: ast.FunctionDef) -> bool:
    """Check if function return type is TypeIs[...] or TypeGuard[...]."""
    ret = func.returns
    if ret is None:
        return False
    if isinstance(ret, ast.Subscript) and isinstance(ret.value, ast.Name):
        return ret.value.id in ("TypeIs", "TypeGuard")
    return False


def _is_variadic(arg: ast.arg, func: ast.FunctionDef) -> bool:
    """Check if arg is *args or **kwargs."""
    return arg.arg in {a.arg for a in [func.args.vararg, func.args.kwarg] if a is not None}


def _is_coroutine_param(node: ast.expr) -> bool:
    """Check if annotation is Coroutine[object, None, T] (first two params allowed)."""
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id == "Coroutine"
    return False


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

            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.annotation is None:
                    continue
                line_num = arg.annotation.lineno
                source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

                if has_bare_ignore(source_line, CHECK_NAME):
                    violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
                    continue
                if is_ignored(source_line, CHECK_NAME):
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

                if _annotation_has_banned_object(arg.annotation):
                    violations.append(
                        report(path, line_num, CHECK_NAME, f"restricted 'object' in annotation of '{arg.arg}'")
                    )

            # Check return annotation
            if node.returns and _annotation_has_banned_object(node.returns):
                line_num = node.returns.lineno
                source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""
                if has_bare_ignore(source_line, CHECK_NAME):
                    violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
                elif not is_ignored(source_line, CHECK_NAME):
                    violations.append(
                        report(path, line_num, CHECK_NAME, f"restricted 'object' in return type of '{node.name}'")
                    )

        # Check variable/attribute annotations (class attrs, module-level)
        if isinstance(node, ast.AnnAssign) and node.annotation:
            line_num = node.annotation.lineno
            source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""

            if has_bare_ignore(source_line, CHECK_NAME):
                violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
            elif not is_ignored(source_line, CHECK_NAME):
                if _annotation_has_banned_object(node.annotation):
                    violations.append(
                        report(path, line_num, CHECK_NAME, "restricted 'object' in variable annotation")
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
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_object_annotations.py -v
```

Expected: PASS

- [ ] **Step 6: Run linter on the script**

```bash
cd /var/home/user1/Projects/coding_rules_python && uv run ruff check reusable/linting/ && uv run basedpyright reusable/linting/
```

- [ ] **Step 7: Commit**

```bash
git add reusable/linting/check_object_annotations.py reusable_tests/fixtures/linting/object_*.py reusable_tests/test_linting/test_check_object_annotations.py
git commit -m "feat(linting): add check_object_annotations script with tests"
```

### Task B4: Create `check_module_mutables.py`

**Files:**
- Create: `reusable/linting/check_module_mutables.py`
- Create: `reusable_tests/fixtures/linting/mutables_pass.py`
- Create: `reusable_tests/fixtures/linting/mutables_fail.py`
- Create: `reusable_tests/fixtures/linting/mutables_ignore.py`
- Create: `reusable_tests/fixtures/linting/mutables_bare_ignore.py`
- Create: `reusable_tests/test_linting/test_check_module_mutables.py`

- [ ] **Step 1: Create test fixtures**

Create `reusable_tests/fixtures/linting/mutables_pass.py`:
```python
"""Fixture: valid module-level state — should PASS."""
from __future__ import annotations

import logging
from typing import Final

# Final constants — allowed
MAX_RETRIES: Final = 3
ALLOWED_TYPES: Final[tuple[str, ...]] = ("json", "yaml")
CONFIG: Final[dict[str, str]] = {"key": "value"}

# Logger — allowed
logger = logging.getLogger(__name__)

# TYPE_CHECKING block — allowed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    _type_registry: dict[str, type] = {}


# Inside functions — allowed
def build_cache() -> dict[str, int]:
    cache: dict[str, int] = {}
    return cache


# Inside classes — allowed
class Manager:
    items: list[str] = []
```

Create `reusable_tests/fixtures/linting/mutables_fail.py`:
```python
"""Fixture: banned module-level mutable state — should FAIL."""
from __future__ import annotations

# Mutable list
_cache: list[str] = []

# Mutable dict
registry: dict[str, int] = {}

# Mutable set
seen = set()

# Constructor calls
items = list()
data = dict()
```

Create `reusable_tests/fixtures/linting/mutables_ignore.py`:
```python
"""Fixture: mutable state with valid ignore — should PASS."""
from __future__ import annotations

_plugin_registry: dict[str, object] = {}  # lint-ignore[module-mutable-state]: plugin system requires mutable registry
```

Create `reusable_tests/fixtures/linting/mutables_bare_ignore.py`:
```python
"""Fixture: mutable state with bare ignore — should FAIL."""
from __future__ import annotations

_cache: list[str] = []  # lint-ignore[module-mutable-state]
```

- [ ] **Step 2: Write tests**

Create `reusable_tests/test_linting/test_check_module_mutables.py`:
```python
"""Tests for check_module_mutables linting script."""
from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path("reusable/linting/check_module_mutables.py")
FIXTURES = Path("reusable_tests/fixtures/linting")


def _run(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(SCRIPT), str(FIXTURES / fixture)],
        capture_output=True,
        text=True,
    )


class TestModuleMutables:
    def test_pass_valid_module_state(self) -> None:
        result = _run("mutables_pass.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_fail_mutable_module_state(self) -> None:
        result = _run("mutables_fail.py")
        assert result.returncode == 1
        assert "[module-mutable-state]" in result.stdout
        # Should catch: list, dict, set, list(), dict()
        assert result.stdout.count("[module-mutable-state]") >= 4

    def test_valid_ignore_silences_check(self) -> None:
        result = _run("mutables_ignore.py")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_bare_ignore_without_rationale_fails(self) -> None:
        result = _run("mutables_bare_ignore.py")
        assert result.returncode == 1
        assert "rationale required" in result.stdout.lower() or "[module-mutable-state]" in result.stdout
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_module_mutables.py -v
```

Expected: FAIL

- [ ] **Step 4: Implement `check_module_mutables.py`**

Create `reusable/linting/check_module_mutables.py`:
```python
"""Check for banned module-level mutable state.

Flags module-level assignments creating mutable containers (list, dict, set)
not wrapped in Final. Allows logger assignments and TYPE_CHECKING blocks.

Usage: python check_module_mutables.py [file1.py file2.py ...]
Ignore with: # lint-ignore[module-mutable-state]: <rationale>
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

CHECK_NAME = "module-mutable-state"

# Mutable literal node types
_MUTABLE_LITERALS = (ast.List, ast.Dict, ast.Set)

# Mutable constructor function names
_MUTABLE_CONSTRUCTORS = {"list", "dict", "set", "defaultdict", "OrderedDict"}

# Logger function names (allowed)
_LOGGER_FUNCS = {"getLogger"}


def _is_final_annotation(annotation: ast.expr | None) -> bool:
    """Check if annotation is Final or Final[...]."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name) and annotation.id == "Final":
        return True
    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        return annotation.value.id == "Final"
    return False


def _is_logger_call(value: ast.expr) -> bool:
    """Check if value is a getLogger(...) or logging.getLogger(...) call."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name) and func.id in _LOGGER_FUNCS:
        return True
    if isinstance(func, ast.Attribute) and func.attr in _LOGGER_FUNCS:
        return True
    return False


def _is_mutable_value(value: ast.expr) -> bool:
    """Check if a value creates a mutable container."""
    if isinstance(value, _MUTABLE_LITERALS):
        return True
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        return value.func.id in _MUTABLE_CONSTRUCTORS
    return False


def _in_type_checking_block(node: ast.stmt, tree: ast.Module) -> bool:
    """Check if a statement is inside an `if TYPE_CHECKING:` block."""
    for top_node in tree.body:
        if isinstance(top_node, ast.If):
            test = top_node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                if node in top_node.body or node in top_node.orelse:
                    return True
    return False


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
            if _is_final_annotation(node.annotation):
                continue
            if _is_logger_call(node.value):
                continue
            if _is_mutable_value(node.value):
                line_num = node.lineno
                source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""
                if has_bare_ignore(source_line, CHECK_NAME):
                    violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
                elif not is_ignored(source_line, CHECK_NAME):
                    violations.append(
                        report(path, line_num, CHECK_NAME, "module-level mutable state — use Final or move into a class/function")
                    )

        # Handle plain assignments: x = [] or x = dict()
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if _is_logger_call(node.value):
                continue
            if _is_mutable_value(node.value):
                line_num = node.lineno
                source_line = source_lines[line_num - 1] if line_num <= len(source_lines) else ""
                if has_bare_ignore(source_line, CHECK_NAME):
                    violations.append(report(path, line_num, CHECK_NAME, "lint-ignore requires rationale after ':'"))
                elif not is_ignored(source_line, CHECK_NAME):
                    violations.append(
                        report(path, line_num, CHECK_NAME, "module-level mutable state — use Final or move into a class/function")
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
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/test_linting/test_check_module_mutables.py -v
```

Expected: PASS

- [ ] **Step 6: Run linter on the script**

```bash
cd /var/home/user1/Projects/coding_rules_python && uv run ruff check reusable/linting/ && uv run basedpyright reusable/linting/
```

- [ ] **Step 7: Commit**

```bash
git add reusable/linting/check_module_mutables.py reusable_tests/fixtures/linting/mutables_*.py reusable_tests/test_linting/test_check_module_mutables.py
git commit -m "feat(linting): add check_module_mutables script with tests"
```

### Task B5: Integration — run all scripts on project code + update root pyproject.toml

**Files:**
- Modify: `pyproject.toml` (root)

- [ ] **Step 1: Run all three scripts on the project's own reusable/ code**

```bash
cd /var/home/user1/Projects/coding_rules_python
python reusable/linting/check_frozen_dataclasses.py reusable/**/*.py
python reusable/linting/check_object_annotations.py reusable/**/*.py
python reusable/linting/check_module_mutables.py reusable/**/*.py
```

Expected: all pass clean (or fix any legitimate violations in reusable/ code, adding lint-ignore with rationale where needed)

- [ ] **Step 2: Run the full test suite**

```bash
cd /var/home/user1/Projects/coding_rules_python && python -m pytest reusable_tests/ -v
```

Expected: all tests pass

- [ ] **Step 3: Add poe tasks to root `pyproject.toml`**

Add after existing `[tool.poe.tasks]`:

```toml
[tool.poe.tasks]
test = "pytest"
lint_objects = "python reusable/linting/check_object_annotations.py"
lint_frozen = "python reusable/linting/check_frozen_dataclasses.py"
lint_mutables = "python reusable/linting/check_module_mutables.py"

[tool.poe.tasks.lint_custom]
sequence = ["lint_objects", "lint_frozen", "lint_mutables"]

[tool.poe.tasks.lint_full]
shell = "basedpyright && ruff check --fix . && ruff format . && poe lint_custom"
```

- [ ] **Step 4: Verify `uv run poe lint_full` passes**

```bash
cd /var/home/user1/Projects/coding_rules_python && uv run poe lint_full
```

Expected: all checks pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add custom lint poe tasks to root pyproject.toml"
```
