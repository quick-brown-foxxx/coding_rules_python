# AI Guide - TODO_PROJECT_NAME

**Authoritative reference for AI agents. Adherence to these standards is mandatory.**

---

## Foundational Philosophy

**YOU MUST read and internalize `docs/PHILOSOPHY.md` before writing any code.** It defines the non-negotiable principles (pit of success, explicitness through types, fail fast, Result-based errors, testing philosophy, architecture, tooling) that drive every decision in this project. All rules below are applications of those principles.

@docs/PHILOSOPHY.md

---

## Critical Reading Path

1. **New context?** Review this document and `docs/PHILOSOPHY.md` fully.
2. **Implementation phase?** Consult [coding_rules.md](docs/coding_rules.md) for detailed patterns.

**Invariant:** Run `uv run poe lint_full` continuously during development, not just at finalization.

---

## Project Overview

<!-- TODO: Fill in project-specific information -->

**Description:** TODO_DESCRIPTION

**Status:** TODO_STATUS

**Key decisions:**
- TODO: List major architectural decisions specific to this project

---

## Toolchain

| Tool            | Purpose                                        |
| --------------- | ---------------------------------------------- |
| Python 3.14+    | Runtime (latest stable, modern type features)  |
| `uv`            | Package management, script execution           |
| `basedpyright`  | Type checking (strict mode, `reportAny=error`) |
| `ruff`          | Linting + formatting (all-in-one)              |
| `pytest`        | Testing framework                              |
| `poethepoet`    | Task runner                                    |
| `rusty-results` | Result pattern for error handling              |

---

## Coding Standards

### Error Handling (Result Pattern)

Errors are return values, not exceptions.

- **Expected failures** (IO, network, user input): return `Result[T, E]`
- **Programming errors** (invalid state, invariants): raise exceptions (fail-fast)
- **Boundaries**: catch third-party exceptions immediately, wrap in `Result`

```python
from rusty_results import Result, Ok, Err

def load_item(item_id: str) -> Result[Item, str]:
    if not exists(item_id):
        return Err(f"Item '{item_id}' not found")
    try:
        return Ok(parse(item_id))
    except ValueError as e:
        return Err(f"Parse error: {e}")
```

### Type Safety

- Strict mode. No `Any`. No `typing.cast()`.
- `TypedDict` for external data shapes. `dataclass` for domain objects.
- Wrap untyped third-party libraries with typed interfaces.

### Async

- All I/O must be async. Never block event loop.
- `asyncio.create_subprocess_exec()` for subprocesses (never `shell=True`)
- For Qt: use `qasync` + `ThreadPoolExecutor` for blocking operations

---

## Architecture

<!-- TODO: Update with project-specific architecture -->

```
Presentation (UI / CLI)
        |
        v
Domain (Business Logic, Models)
        |
        v
Utilities (Helpers, Wrappers)
```

Dependencies flow downward only. UI never imported by lower layers.

---

## Key Workflows

<!-- TODO: Document project-specific workflows -->

| Goal                       | Command                                   |
| -------------------------- | ----------------------------------------- |
| Lint + type check + format | `uv run poe lint_full`                    |
| Run tests                  | `uv run poe test`                         |
| Run application            | `uv run poe app`                          |
| Pre-commit check           | `uv run poe lint_full && uv run poe test` |

---

## Ambiguity Resolution

If requirements are unclear, halt and request clarification from the developer.
