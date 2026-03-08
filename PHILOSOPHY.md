# Python Development Philosophy

This document defines the foundational beliefs that drive all coding decisions.
Every other document in this collection inherits from and applies these principles to specific domains.

---

## 1. The Pit of Success

Build systems where doing things correctly is the path of least resistance.
Instead of relying on conventions that developers must remember, construct boundaries that make violations impossible.

- Strict type checking that rejects ambiguity at compile time
- Linters that enforce rules automatically, not through code review
- Architecture that separates concerns structurally, not by agreement
- Error handling that forces callers to address failures, not ignore them

**The investment is front-loaded.** We spend time setting up types, linters, libraries, and architecture to minimize time spent on bug fixes, manual testing, and debugging later. Python by default is dynamic and implicit — we actively work against that default.

## 2. Explicitness Through Types

Everything should be known before runtime. We always know what types and values we have. We always know whether we are on the error path or the success path.

- **Strict type checking is non-negotiable.** basedpyright in strict mode, `reportAny=error`. No `Any`, no `typing.cast()`, no unvalidated `# type: ignore`.
- **Errors are values, not exceptions.** Use `Result[T, E]` for expected failures. Exceptions are reserved for programming errors (impossible states, invariant violations) — they mean "this is a bug."
- **Data has shape.** Use `TypedDict` for external data (JSON, configs, APIs). Use `dataclass` for domain objects. Never pass raw `dict` through business logic.
- **Dynamic boundaries get wrapped.** Third-party libraries with weak typing get typed wrappers. Untyped data from outside (user input, network, files) gets validated and narrowed immediately at the boundary.

The goal: if the type checker says it's correct, it runs correctly. If something can fail, the type signature says so.

## 3. Fail Fast, Fail Early

Detect problems at the earliest possible moment. Compile time is better than runtime. Startup is better than mid-operation. Explicit error is better than silent corruption.

- **Validate preconditions** at the entry of each subsystem: required permissions, installed dependencies, valid configuration, sane inputs
- **Validate postconditions** where output correctness matters
- **No escape hatches.** Don't allow `Any`, `cast()`, blanket `type: ignore`, or `except Exception: pass` to silently bypass the safety net
- **Type narrowing over assumptions.** When a value could be multiple types, narrow it with `isinstance`, `TypeIs`, or pattern matching — never assume

## 4. Error Handling as Control Flow

Errors are a normal part of program execution, not exceptional events. The type system should track them.

- **Expected failures** (IO, network, user input, missing files): return `Result[T, E]` — the caller must handle both paths
- **Programming errors** (violated invariants, impossible states): raise exceptions — these are bugs, the program should crash
- **Third-party boundaries**: catch library exceptions immediately, convert to `Result` — don't let foreign exception hierarchies leak through layers
- **Error boundaries**: UI/CLI layers catch all remaining errors and present user-friendly messages. Business logic never swallows errors silently
- **Early returns**: handle the error case first, keep the success path unindented and linear

## 5. Testing Philosophy

Tests exist to prove that features work, not to produce green checkmarks.

- **Trustworthiness over coverage.** A test that mocks away the thing it's testing proves nothing. Coverage numbers are a guideline, not a goal.
- **E2e and CLI tests are the primary safety net.** They test real behavior through real code paths. 5 good e2e tests give more confidence than 100 unit tests with heavy mocking.
- **Unit tests for pure logic.** Functions that transform data without side effects — these are worth unit testing because they're honest.
- **Real over mocked.** Prefer real HTTP servers over patched requests. Prefer real process execution over mocked subprocess. Prefer real file systems (via tmp dirs) over mocked IO. When mocking is necessary, build real-like custom implementations rather than monkey-patching runtime.
- **20/80 rule.** Invest test effort where it gives the most confidence. Don't chase 100% coverage in utilities while core workflows go untested.
- **Two tiers of infrastructure.** Lightweight (pytest, fixtures, markers) for most projects. Heavyweight (containers, mock servers, isolated environments) when the project warrants investment.

## 6. Architecture: Separation by Responsibility

Separate what changes for different reasons. Separate what should be testable independently.

- **Layered dependency flow:** Presentation (UI/CLI) -> Domain (business logic) -> Utilities. Never upward.
- **UI is a plugin.** The same business logic serves Qt GUI, CLI, and potentially API (FastAPI). The core never imports from UI. Adding a new interface should not require changing business logic.
- **Data vs. logic.** Domain types (dataclasses) carry data. Services and managers operate on data. Utilities are stateless pure functions. Stateful classes exist for managing lifecycle and continuous state — but their state is explicit, not hidden.
- **Scale-appropriate separation.** In large projects: separate files, directories, layers. In single scripts: separate functions, clear sections within one file. The principle is the same; the implementation scales.
- **Wrap third-party libraries.** Isolate external dependencies behind typed interfaces. This gives type safety, testability, and the ability to swap implementations. Enforce wrapper usage via linter rules (ruff `banned-api`) where possible.

## 7. Tooling: Fast, Strict, Modern

Use tools that enforce the philosophy automatically. Prefer tools that are fast, opinionated, and all-in-one over legacy alternatives.

- **`uv`** for package management and script execution — fast, handles PEP 722 inline scripts
- **`basedpyright`** for type checking — strict mode, faster than mypy, catches more
- **`ruff`** for linting and formatting — replaces black, isort, flake8, bandit in one tool
- **`pytest`** for testing — with plugins as needed (pytest-qt, pytest-asyncio, pytest-httpserver)
- **`poethepoet`** for task running — simple task definitions in pyproject.toml
- **`pre-commit`** for git hooks — automates linting, formatting, type checking on every commit
- **PEP 722 inline metadata** for single-file scripts — dependencies declared in the script, not in separate files
- **Prefer packages without system deps.** PySide6 over PyQt (no extra system libraries). Pure Python or wheels over packages requiring C compilation.
- **Python version: latest stable.** Use modern features (generic syntax, TypeIs, match statements). Don't target old versions unless required.

## 8. CLI: typer. GUI: PySide6. Text output: Jinja2

Standard tools for standard tasks:

- **CLI**: typer for all projects with `uv`. argparse only for stdlib-only scripts without external deps.
- **GUI**: PySide6 with qasync for async integration (QtAsyncio is still in technical preview). Never block the event loop.
- **Text generation** (HTML, configs, reports): Jinja2 templates. Separate data from presentation.
- **HTTP**: httpx (async-capable). Logging: colorlog. Config: YAML + JSON Schema validation.
- **Async**: for all I/O operations. `asyncio.create_subprocess_exec()` for subprocesses. Never `subprocess.run()` in async context. Never `time.sleep()` in event loops.

## 9. Project Setup: Invest Early

Every project, no matter how small, starts with the safety net configured:

- **Single script**: PEP 722 metadata, pyproject.toml for tool config (ruff + basedpyright), shebang for direct execution
- **Full project**: src layout, AGENTS.md, coding_rules.md, pyproject.toml with all tools, pre-commit hooks, test directory structure
- **The overhead is worth it.** Spending 10 minutes on setup saves hours of debugging implicit failures later. This is the pit of success in action.
