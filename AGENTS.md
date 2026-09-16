# Python Auxiliary Skills for myai

Also see @README.md

This repository is an **auxiliary skill pack** for the [myai](https://github.com/quick-brown-foxxx/myai) agent skill system. It provides Python-specific tooling, patterns, and conventions that extend myai's language-agnostic SDLC workflows.

## Relationship to myai

**myai is a prerequisite.** Install myai first, then add these Python skills. myai provides the generic workflows: engineering principles, planning, implementation, testing, debugging, code review, CI/CD, security, performance, and agent orchestration. This repo adds the Python-specific layer on top.

Think of it as: **myai = the engine and chassis; this repo = the Python body kit.** The generic philosophy (pit of success, fail fast, error handling as control flow, testing trustworthiness over coverage, architecture separation by responsibility) lives in myai's canonical `engineering-principles` skill. The skills here keep only Python-specific tooling, library choices, and patterns.

## What's Here

### Python Skills (11)

Each skill is a Python-specific extension of one or more myai parent skills. Load the myai parent first, then load the Python extension.

| Python Skill | myai Parent(s) | Description |
|---|---|---|
| `writing-python-code` | `engineering-principles` | basedpyright strict typing, `Result[T,E]` error handling, async patterns, code style, security |
| `python-reliable-subprocess-handling` | `engineering-principles` | asyncio subprocess timeout/cancel output loss, orphaned children holding pipes, output tails, test doubles |
| `testing-python` | `high-level-testing-strategy`, `test-driven-development`, `manual-testing` | pytest fixtures, CLI/e2e tests, containerized testing, mock servers, pytest-qt |
| `architecting-python-changes` | `architecting-changes` | Python-specific architecture router: boundaries, wrappers, reusable cores, framework choices |
| `setting-up-python-projects` | `engineering-principles`, `setting-up-projects` | Bootstrap general Python projects: uv, ruff, basedpyright, pre-commit, src layout, templates |
| `setting-up-python-backends` | `engineering-principles`, `architecting-changes`, `setting-up-backends` | Backend/API bootstrap: FastAPI/Django, app factory, migrations, service-first layout |
| `setting-up-logging` | `engineering-principles` | colorlog setup, file/stdout logging modes, CLI user output helpers, QML log routing |
| `setting-up-shortcuts` | `engineering-principles` | PySide6 keyboard shortcuts with TOML config and platform-specific defaults |
| `building-multi-ui-apps` | `architecting-changes` | Multi-interface apps: reusable core, thin CLI/GUI/API adapters, composition root, entry routing |
| `building-qt-apps` | `architecting-changes`, `engineering-principles` | PySide6 desktop apps: qasync, Manager→Service→Wrapper, signals, QML, XDG portals |
| `repair-opencode-kilo-python-lsp-diagnostics` | (standalone — no myai parent) | Fix Kilo/opencode LSP (pyright) not resolving third-party imports; only for Kilo/opencode |

### Adding and Editing Skills

When adding, removing, or renaming a skill, keep the skill catalogs in sync. The agent MUST update these docs in the same change:

- `README.md` — the skills table (and the "N Python skills" count)
- `AGENTS.md` — the skills table, the "(N)" count in the section heading, and the `skills/` mention in `## What's Here`

If the skill is a Python-specific extension of a myai skill, also check whether the new skill should be cross-referenced from the "Related myai Skills" sections of sibling skills in `skills/`.

### Shared Code Modules

Copy-paste building blocks for new projects (not an installable library). On bootstrap they render into the downstream repo as:

- `src/<package>/shared/logging/` — colorlog-based file + stdout logging, colored non-log CLI output (`write_info`, `write_error`, etc.)
- `src/<package>/shared/shortcuts/` — PySide6 keyboard shortcut manager with TOML config, platform defaults, and Qt integration
- `src/<package>/shared/subprocess.py` — cancellation-safe asyncio subprocess runner (timeout, tree kill, output cap, captured output)
- `tools/linting/` — AST-based custom lint checks (dev-only)
- `shared_tests/` — tests for the copied shared modules and lint checks

Canonical sources live at the repo root: `shared/logging/`, `shared/shortcuts/`, `shared/subprocess.py`, `tools/linting/`, `shared_tests/`. Imports become `<package>.shared.logging` / `<package>.shared.shortcuts` / `<package>.shared.subprocess` downstream (runtime code uses relative imports so it copies verbatim).

### Templates (`templates/`)

Copy into new projects, fill TODOs, and customize:

- `AGENTS.md` — Agent orientation template (references Python skills only; myai skills are assumed available)
- `pyproject.toml` — Full tooling config: uv, ruff, basedpyright, pytest, poethepoet
- `pre-commit-config.yaml` — Git hooks for linting, formatting, type checking
- `.gitignore`, `.vscode/` — Editor and VCS defaults
- `.github/workflows/ci.yml` — Cross-platform CI (Linux + Windows) rendered into downstream repos

### Rules (`rules/`)

- `coding_rules.md` — Full Python coding standards (copy to `docs/` in new projects)

### For AI Agents Working in This Repo

- Load `architecting-python-changes` when a feature, fix, or refactor requires architecture decisions
- For new backend repos, start with `setting-up-python-backends`, then pull generic pieces from `setting-up-python-projects`
- Load `building-backends` (myai) for backend structure decisions and `writing-python-code` for implementation rules
- Load `building-multi-ui-apps` when CLI, GUI, and API share business logic
- Load `building-qt-apps` for PySide6-specific architecture, signals, and async integration

## Key Conventions

- **Run everything through `uv`**: `uv run pytest`, `uv run ruff`, `uv run basedpyright`, `uv run poe`
- **Type checking**: basedpyright strict mode, `reportAny=error` — no `Any`, no unvalidated `# type: ignore`
- **Error handling**: `Result[T, E]` from rusty-results for expected failures; exceptions = bugs only
- **Data validation**: `msgspec.Struct` for external data; `pydantic` at FastAPI edge only, convert immediately
- **CLI**: typer (argparse only for stdlib-only scripts); always enable `-h` support
- **GUI**: PySide6 + qasync (not QtAsyncio — still in technical preview)
- **HTTP**: httpx (async-capable)
- **Text output**: Jinja2 templates
- **Testing**: pytest; e2e/CLI tests as primary safety net; real over mocked
- **Pre-commit**: `uv run poe lint_full` passes, `uv run poe test` passes before every commit

## Cross-Platform

Default: mature projects (packages, apps, multi-UI, Qt) target Windows, macOS, and Linux equally. A deliberately OS-specific project is the exception; standalone/small scripts may stay OS-specific.

- Use `pathlib`; `platformdirs` for user config/data/cache/log dirs. Never hardcode `~/.config` or `~/Library/Application Support`.
- No POSIX-only commands or syscalls in cross-platform code.
- Tiny OS difference → narrow `sys.platform` / `os.name` branch. Complex OS-specific subsystem → `Protocol` with one impl per OS (see `building-multi-ui-apps`).
- Dev helpers: `poe` tasks and `pyproject.toml` scripts never shell out to POSIX tools. Use cross-platform abstractions or a python helper.
- Enforcement: CI (`.github/workflows/ci.yml`) runs lint + tests on Linux and Windows; `templates/.github/workflows/ci.yml` ships the same to downstream repos.
