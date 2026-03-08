---
name: writing-python-code
description: Use when writing any Python code - establishing type safety, error handling, and tooling standards before implementation
---

# Writing Python Code

## Overview

All Python code follows the pit-of-success philosophy: strict types, Result-based error handling, modern tooling. This skill routes to specific sub-skills based on project type.

## Core Rules (Always Apply)

1. **basedpyright strict** with `reportAny=error`. No `Any`, no `cast()`, no blanket `type: ignore`.
2. **Result pattern** (`rusty-results`): expected failures return `Result[T, E]`, exceptions only for bugs.
3. **Early returns**: handle error path first, keep success path linear.
4. **Validate early**: preconditions at subsystem entry points.
5. **Typed data**: `TypedDict` for external data, `dataclass` for domain objects, never raw `dict`.
6. **Async for I/O**: never block event loop, never `shell=True`, never `time.sleep()` in async.
7. **Run `uv run poe lint_full` continuously**, not just at the end.

## When to Use Which Skill

- **Single script / small automation** -> `write-single-python-script`
- **New project setup** -> `setup-python-project`
- **Qt/GUI work** -> `working-with-qt`
- **Error handling patterns** -> `python-error-handling`
- **Writing tests** -> `python-testing-lightweight` or `python-testing-heavyweight`
- **Multi-interface app (GUI+CLI+API)** -> `multi-ui-architecture`

## Quick Reference

| Tool | Purpose |
|------|---------|
| `uv` | Package management, script execution |
| `basedpyright` | Type checking (strict) |
| `ruff` | Lint + format |
| `pytest` | Testing |
| `rusty-results` | Result[T, E] pattern |
| `typer` | CLI framework (preferred) |
| `argparse` | CLI only for stdlib-only scripts |
| `PySide6` | GUI (no system deps) |
| `httpx` | HTTP (async) |
| `Jinja2` | Text output generation |

## Style

- Line length: 120. Double quotes. 4-space indent.
- `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE` constants.
- Google-style docstrings on public APIs.
- Commits: `<type>(<scope>): <subject>`
