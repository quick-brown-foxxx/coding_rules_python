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

**Invariant:** Treat `uv run poe lint_full` + `uv run poe test` as the standard verification flow. Run `uv run poe lint_full` continuously during development, not just at finalization.

**Command policy:** Run project-local Python tools through `uv`, not system-installed binaries. Use `uv run python`, `uv run pytest`, `uv run ruff`, `uv run basedpyright`, `uv run poe`, and `uv run pre-commit`.

---

### Skills — ALWAYS CHECK, ALWAYS USE

<EXTREMELY_IMPORTANT>

**BEFORE writing ANY code, ALWAYS check available skills and USE every skill that matches your scope.** Skills are project standards — code that ignores them WILL fail review. When delegating to subagents, tell them which skills to use.

#### Python

- `architecting-python-changes` — ALWAYS load when planning a new feature, non-trivial fix, or refactor that may affect structure, layering, wrappers, or library choice, or when deciding where code should live. NEVER make architecture decisions blindly.
- `writing-python-code` — ALWAYS load when writing/editing Python. NEVER write Python without this.
- `testing-python` — ALWAYS load when writing tests or fixtures. NEVER write pytest tests without this.
- `setting-up-python-projects` — ALWAYS load when bootstrapping a new general package or app. NEVER set up pyproject.toml manually.
- `setting-up-python-backends` — ALWAYS load when bootstrapping a backend, API service, or worker-oriented repo. Start here for service repos, then borrow generic bootstrap pieces from `setting-up-python-projects` as needed. NEVER scaffold Python backends blindly.
- `writing-python-scripts` — ALWAYS load when creating standalone scripts. NEVER write single-file CLI tools without this.
- `setting-up-logging` — DO load when adding or changing logging. DON'T configure logging manually.
- `building-python-backends` — DO load when shaping backend/service/API/workers architecture. DON'T mix transport, domain, and infrastructure blindly.
- `building-multi-ui-apps` — DO load when app has both CLI and/or GUI and/or API sharing logic. DON'T duplicate business logic across interfaces.

</EXTREMELY_IMPORTANT>

---

## Project Overview

<!-- TODO: Fill in project-specific information -->

**Description:** TODO_DESCRIPTION

**Status:** TODO_STATUS

**Key decisions:**
- TODO: List major architectural decisions specific to this project

<!-- if building-qt-apps -->
- XDG Desktop Portal file dialogs via `QT_QPA_PLATFORMTHEME=xdgdesktopportal` (set at GUI startup)
- `qasync` for Qt + asyncio integration in GUI mode
<!-- endif building-qt-apps -->

---

## Toolchain

| Tool            | Purpose                                        |
| --------------- | ---------------------------------------------- |
| Python 3.14+    | Runtime (latest stable, modern type features)  |
| `uv`            | Package management, script execution           |
| `basedpyright`  | Type checking (strict mode, `reportAny=error`) |
| `ruff`          | Strict linting + formatting |
| `pytest`        | Testing framework                              |
| `poethepoet`    | Task runner                                    |
| `rusty-results` | Result pattern for error handling              |

All commands in this project are assumed to run inside the `uv`-managed environment.

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
- `msgspec.Struct` for configs and non-framework external data. In FastAPI apps, `pydantic` DTOs should live at the HTTP edge only and must be converted immediately into framework-free typed structures. `dataclass` for domain objects.
- Wrap untyped third-party libraries with typed interfaces.

### Async

- All I/O must be async. Never block event loop.
- `asyncio.create_subprocess_exec()` for subprocesses (never `shell=True`)
- For Qt: use `qasync` + `ThreadPoolExecutor` for blocking operations

---

## Architecture

<!-- TODO: Update with project-specific architecture -->

```
Presentation / Adapters (UI / CLI / API / workers)
        |
        v
Domain / Application (Business Logic, Models, Use Cases)
        |
        v
Infrastructure / Utilities (DB, clients, wrappers, helpers)
```

Dependencies flow downward only. Presentation never imported by lower layers. Backend projects usually make the infrastructure layer explicit.

---

## Key Workflows

<!-- TODO: Document project-specific workflows -->

| Goal                                      | Command                                   |
| ----------------------------------------- | ----------------------------------------- |
| Type check + Ruff + custom linters        | `uv run poe lint_full`                    |
| Run tests                                 | `uv run poe test`                         |
| Run primary app or service                | `TODO_PROJECT_RUN_COMMAND`                |
| Pre-commit verification                   | `uv run poe lint_full && uv run poe test` |

---

## Ambiguity Resolution

If requirements are unclear, halt and request clarification from the developer.
