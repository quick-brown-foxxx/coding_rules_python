# Coding Rules Improvements — Design Spec

## Context

The project at `/var/home/user1/Projects/coding_rules_python/` contains Python coding standards, rules, and AI skills. The philosophy centers on: pit of success, explicitness through types, fail fast, errors as values (Result[T,E]), and strict tooling.

Review identified 8 improvements + inconsistency fixes, all aligned with the existing philosophy. Line limit per skill file: 550-600 lines.

## Changes

### 1. Restrict `object` to boundary/guard positions only

**Current state:** Rules say "use `object` instead of `Any`" — too permissive, agents abuse it like Any.

**New rule:** `object` is only allowed in:

- TypeIs/TypeGuard parameters: `def is_valid(obj: object) -> TypeIs[Config]`
- Signal handlers: `*_args: object`
- Coroutine type params: `Coroutine[object, None, T]`
- Logging/debug utilities that genuinely accept anything printable
- `Signal(object)` in PySide6 (document as limitation — no generic signals)

Banned uses (with replacements):

- `dict[str, object]` → `msgspec.Struct`, `TypedDict`, or explicit value union
- `list[object]` / `Sequence[object]` → `TypeVar` or `Protocol`
- Function params typed `object` when real type is knowable → narrow the type

**Files to change:**

- `rules/coding_rules.md` line 21: rewrite the `Any` → `object` banned patterns row. Split into two rows: `Any` → banned entirely, `object` → restricted to boundary positions. Add brief "allowed uses" note (~5 net new lines)
- `rules/coding_rules_short.md`: update the "No Any" bullet to mention object restriction
- `skills/writing-python-code/SKILL.md` line 44: same table rewrite. Update the "Handling Any at Library Boundaries" section header/intro to reflect tighter object rules (~0 net new lines, rewrite existing)
- `skills/building-qt-apps/SKILL.md` line 208: add note that `Signal(object)` is a PySide6 limitation, not a recommendation (+1 line)

### 2. Immutability by default

**New rule (for `coding_rules.md` section Type System, new section 1.6 "Immutability"):**

- `frozen=True` is the default for dataclasses. Mutable dataclasses require justification.
- Return `tuple` over `list` for fixed collections.
- Use `Sequence` (not `list`) in function parameters that don't mutate the collection.
- `frozenset` over `set` when mutation isn't needed.

~15 lines including a small example.

**Files:** `coding_rules.md` (add section), `writing-python-code/SKILL.md` (update dataclass example to show `frozen=True`), `coding_rules_short.md` (add one bullet)

### 3. Dependency Injection — Manual composition root

**Research conclusion:** All DI libraries either break basedpyright strict (`dependency-injector` has known pyright issues), add unnecessary runtime reflection (`injector`, `punq`), or are too new (`dioxide`). Manual constructor injection is perfectly type-safe, zero-dependency, and PySide6-friendly.

**New rule:** Pass dependencies via constructor parameters with Protocol-typed interfaces. A single composition root function (`create_app()` / `create_domain()`) at the entry point wires everything. Domain classes never instantiate their own infrastructure dependencies.

**Pattern for Qt app:**

```python
# app/bootstrap.py
def create_app(config: AppConfig) -> MainWindow:
    """Composition root — the ONLY place we wire dependencies."""
    db = DatabaseWrapper(config.db_path)
    api = ApiClientWrapper(config.api_url, config.api_key)
    auth = AuthService(api_client=api)
    sync = SyncService(db=db, api_client=api)
    session = SessionManager(auth=auth, sync=sync)
    return MainWindow(session=session)
```

**Pattern for multi-UI:**

```python
def create_domain(config: AppConfig) -> SessionManager:
    """Shared domain — used by both CLI and GUI."""
    db = DatabaseWrapper(config.db_path)
    auth = AuthService(api_client=ApiClientWrapper(config.api_url))
    return SessionManager(auth=auth)

# GUI: window = MainWindow(session=create_domain(config))
# CLI: cli_app = build_typer_app(session=create_domain(config))
```

**Pattern for testing:**

```python
def test_sync_handles_conflict() -> None:
    db = FakeDatabaseWrapper()
    api = FakeApiClient(responses=[CONFLICT_RESPONSE])
    sync = SyncService(db=db, api_client=api)
    result = sync.pull_changes()
    assert result.is_err
```

~30 lines.

**Files:** `building-multi-ui-apps/SKILL.md` (add section — has 352 lines of headroom, this is the natural home). Add a brief cross-reference from `building-qt-apps/SKILL.md` (~1 line).

### 4. String typing with NewType

**New rule (for `coding_rules.md` section Type System, new subsection):**
Use `NewType` for domain identifiers and typed strings that should not be interchangeable. Use `Path` for filesystem paths, never `str`.

```python
from typing import NewType
ProfileId = NewType("ProfileId", str)
UserId = NewType("UserId", str)

def delete_profile(profile_id: ProfileId) -> Result[None, str]: ...
# delete_profile(user_id)  # type error — caught at check time
```

~10 lines.

**Files:** `coding_rules.md` (add subsection), `coding_rules_short.md` (add one bullet)

### 5. Enum vs Literal vs Union decision table

**New rule (for `coding_rules.md` section Type System):**

| Use case | Tool |
|----------|------|
| Small fixed string set in function params (mode flags) | `Literal["json", "yaml"]` |
| Value set with behavior, iteration, or in data models | `StrEnum` |
| Structurally different variants | Union type: `type Outcome = Success \| Failure` |
| C/binary protocol interop | `IntEnum` |

~8 lines.

**Files:** `coding_rules.md` only.

### 6. Module-level mutable state ban

**New rule (for `coding_rules.md` section Architecture):**
Module-level mutable state is banned. All module globals must be `Final`. Registries, caches, and singletons belong in explicitly constructed objects passed via DI. Exceptions: `logging.getLogger()` and `Final` constants.

~5 lines.

**Files:** `coding_rules.md` only.

### 7. Function signature discipline

**New rule (for `coding_rules.md` section Code Style):**
Maximum 5 parameters per function. Beyond that, group into a config dataclass/struct. Ban boolean flag parameters that switch behavior — use two named functions or an enum. Functions in the same module with similar purposes must have consistent parameter ordering.

~8 lines.

**Files:** `coding_rules.md` only.

### 8. Circular imports = architectural bug

**New rule (for `coding_rules.md` section Architecture):**
Circular imports are architectural bugs, not something to work around with `TYPE_CHECKING`. If two modules import each other, one dependency must be inverted (extract a Protocol, move shared types to a common module, or restructure layers). `TYPE_CHECKING` is only for forward references within the same layer, not for hiding cycles. Enforce layer boundaries with ruff `banned-api` where practical.

~8 lines.

**Files:** `coding_rules.md` (rewrite existing TYPE_CHECKING mention in architecture context), `writing-python-code/SKILL.md` (add brief note to existing TYPE_CHECKING section that it's not for hiding circular deps — ~2 lines)

### 9. Fix existing inconsistencies

**`dict[str, object]` replacements (5 instances):**

- `notes/other-patterns.md:36-37,51` — replace `dict[str, object]` with `dict[str, str | int | bool | list[str]]` or a typed structure appropriate for config merging context
- `skills/testing-python/SKILL.md:381` — replace `profiles: dict[str, dict[str, object]]` with a typed `ProfileData` TypedDict
- `skills/writing-python-code/SKILL.md:149` — replace `data: Required[dict[str, object]]` with a more precise type in the ValidResponse example

**`Signal(object)` documentation:**

- `skills/building-qt-apps/SKILL.md:208` — change "Use typed signals: `Signal(str)`, `Signal(float)`, `Signal(object)`" to note that `Signal(object)` is a PySide6 limitation (no generic signals), not a first choice

## Line impact estimates

| File | Current | Estimated after | Status |
|------|---------|----------------|--------|
| `coding_rules.md` | 377 | ~440 | Well under 600 |
| `coding_rules_short.md` | 39 | ~42 | Fine |
| `writing-python-code/SKILL.md` | 512 | ~515 | Under 550 (rewrites, not additions) |
| `building-qt-apps/SKILL.md` | 448 | ~450 | Fine |
| `building-multi-ui-apps/SKILL.md` | 148 | ~180 | Fine |
| `testing-python/SKILL.md` | 423 | ~425 | Fine |
| `notes/other-patterns.md` | 60 | ~60 | Fine |
| `PHILOSOPHY.md` | 101 | 101 | No changes |

## 10. Automated enforcement

### 10a. Config-only wins (ruff + basedpyright)

Add to `templates/pyproject.toml` and reference from skills:

```toml
# ruff — function signature discipline
[tool.ruff.lint]
extend-select = [
    "PLR",   # pylint refactor (includes PLR0913 — max args)
    "FBT",   # flake8-boolean-trap (FBT001, FBT002)
]

[tool.ruff.lint.pylint]
max-args = 5

# basedpyright — circular import detection
[tool.basedpyright]
reportImportCycles = "error"
```

**Files:** `templates/pyproject.toml`, `writing-python-code/SKILL.md` (basedpyright config block), `setting-up-python-projects/SKILL.md` (mention in setup checklist)

### 10b. Custom linting scripts (`reusable/linting/`)

Three pure-stdlib AST-based scripts (no dependencies beyond Python stdlib). Each is a standalone PEP 722 script runnable via `uv run`. Designed to run as pre-commit hooks.

**Shared conventions across all three scripts:**

- **Ignore mechanism:** Each check supports an inline ignore comment with required rationale:
  `# lint-ignore[check-name]: rationale here`
  The rationale is mandatory — bare `# lint-ignore[check-name]` without text after `:` is reported as an error. This mirrors the existing `# type: ignore[code] # rationale: <reason>` pattern.
- **Exit codes:** 0 = clean, 1 = violations found.
- **Output format:** `file.py:line: [check-name] message`
- **Input:** Accept file paths as CLI args (for pre-commit integration). If no args, scan current directory recursively for `.py` files.
- **Pure stdlib:** `ast` + `sys` + `pathlib` only. No external dependencies.

**Script 1: `check_object_annotations.py`** (~80-100 lines)

Check name: `restricted-object`

Walks all type annotations in function signatures, variable annotations, and class attributes. Flags:
- `dict[str, object]` or any `dict[..., object]`
- `list[object]`, `Sequence[object]`, `tuple[object, ...]`
- Bare `object` as a function parameter type (except whitelisted positions)

Whitelist (allowed uses — not flagged):
- `TypeIs` / `TypeGuard` parameter: `def foo(obj: object) -> TypeIs[X]`
- Variadic args: `*args: object`, `**kwargs: object`
- `Coroutine[object, None, T]` (first two type params)
- Logging/debug: configurable via `# lint-ignore[restricted-object]: logging utility`

**Script 2: `check_frozen_dataclasses.py`** (~40-50 lines)

Check name: `unfrozen-dataclass`

Finds `@dataclass` and `@dataclass(...)` decorators. Flags any that don't include `frozen=True`.

Whitelist:
- `# lint-ignore[unfrozen-dataclass]: builder pattern` or similar rationale
- `@dataclass(frozen=True)` — obviously fine
- `@dataclass(frozen=True, slots=True)` — fine regardless of other args

**Script 3: `check_module_mutables.py`** (~60-80 lines)

Check name: `module-mutable-state`

Flags module-level (top-level, not inside functions/classes) assignments that create mutable containers:
- `x = []`, `x = {}`, `x = set()`, `x: list[...] = []`, `x: dict[...] = {}`
- `x = list()`, `x = dict()`, `x = set()`
- `x = defaultdict(...)`, `x = OrderedDict()`

Whitelist:
- Anything annotated with `Final`: `x: Final[dict[str, str]] = {}`
- `# lint-ignore[module-mutable-state]: rationale`
- Assignments inside `if TYPE_CHECKING:` blocks
- Logger assignments: `logger = getLogger(...)`, `logger = logging.getLogger(...)`

**Tests (`reusable_tests/test_linting/`):**

Each script gets a test module with:
- Valid code that should pass (no violations)
- Code with violations that should be caught
- Code with valid `# lint-ignore[check-name]: rationale` that should be silenced
- Code with bare `# lint-ignore[check-name]` (no rationale) that should still be flagged
- Edge cases (nested functions, class methods, TYPE_CHECKING blocks, etc.)

Tests use `subprocess.run` to invoke the scripts against fixture `.py` files in `reusable_tests/fixtures/linting/`, checking exit codes and output.

**Poe tasks (in `templates/pyproject.toml`):**

```toml
[tool.poe.tasks]
lint_objects = "python reusable/linting/check_object_annotations.py"
lint_frozen = "python reusable/linting/check_frozen_dataclasses.py"
lint_mutables = "python reusable/linting/check_module_mutables.py"
lint_custom = ["lint_objects", "lint_frozen", "lint_mutables"]

[tool.poe.tasks.lint_full]
shell = "basedpyright . && ruff check --fix . && ruff format . && poe lint_custom"
```

Individual tasks for running each check separately, `lint_custom` for all custom checks, and `lint_full` updated to include them.

**Pre-commit integration:**

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-object-annotations
      name: Check restricted object annotations
      entry: uv run reusable/linting/check_object_annotations.py
      language: system
      types: [python]
    - id: check-frozen-dataclasses
      name: Check frozen dataclasses
      entry: uv run reusable/linting/check_frozen_dataclasses.py
      language: system
      types: [python]
    - id: check-module-mutables
      name: Check module mutable state
      entry: uv run reusable/linting/check_module_mutables.py
      language: system
      types: [python]
```

## Implementation order

Two parallel tracks:

**Track A — Documentation updates (items 1-9):**
1. Fix inconsistencies first (examples that violate current rules)
2. `coding_rules.md` — add all new sections (items 2, 4, 5, 6, 7, 8)
3. `coding_rules.md` + `writing-python-code/SKILL.md` — rewrite `object` guidance (item 1)
4. `building-multi-ui-apps/SKILL.md` — add DI composition root section (item 3)
5. `coding_rules_short.md` — update with new bullet points
6. Minor cross-reference additions to `building-qt-apps/SKILL.md`
7. Config updates: `templates/pyproject.toml` (ruff PLR/FBT + basedpyright reportImportCycles)

**Track B — Linting scripts (item 10b):**
1. Create `reusable/linting/` directory with three scripts
2. Create `reusable_tests/test_linting/` with test fixtures and test modules
3. Validate all scripts pass on the project's own code
4. Add pre-commit hook entries to `templates/pre-commit-config.yaml`

Track B is a separate coding task — spawn coder agent, then validator.

## Out of scope

- `None` discouragement — already covered by the Result pattern, no changes needed
- FastAPI/web API DI patterns — will be a separate skill later
- DI libraries — manual injection is the recommendation, no library needed
- PHILOSOPHY.md changes — all improvements are applications of existing philosophy, not new principles
