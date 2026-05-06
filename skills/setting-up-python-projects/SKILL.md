---
name: setting-up-python-projects
description: >
  ALWAYS LOAD THIS SKILL WHEN CREATING A NEW PYTHON PROJECT OR SETTING UP PROJECT STRUCTURE. Do not scaffold or bootstrap Python projects directly — use this skill first.
  Bootstrap new Python projects: directory structure, pyproject.toml, pre-commit, uv sync.
---

# Setting Up Python Projects

New projects start with the full safety net configured. The bootstrap flow is local and explicit: promote the template files into their final locations, copy `shared/` and `shared_tests/`, copy the docs references into `docs/`, then customize.

Make sure to read repo's readme.

---

## Project Layout

```
project/
├── src/appname/
│   ├── __init__.py           # __version__ = "0.1.0"
│   ├── __main__.py           # Entry point
│   ├── constants.py          # Shared constants
│   ├── core/                 # Business logic
│   │   ├── models.py         # Data types (dataclasses)
│   │   ├── manager.py        # Business operations
│   │   └── exceptions.py     # Custom exception hierarchy
│   ├── cli/                  # CLI interface
│   │   ├── commands.py       # Command implementations
│   │   ├── parser.py         # Argument parsing
│   │   └── output.py         # Formatted output helpers
│   ├── ui/                   # Qt GUI (if applicable)
│   │   ├── main_window.py
│   │   ├── dialogs/
│   │   └── widgets/
│   ├── utils/                # Stateless utilities
│   │   ├── paths.py
│   │   └── logging.py
│   ├── wrappers/             # Third-party lib wrappers
│   │   └── some_wrapper.py
│   └── stubs/                # Type stubs for untyped libs
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py
├── scripts/                  # Dev utilities
│   ├── bootstrap.py          # Setup script
│   └── check_type_ignore.py
├── docs/
│   ├── coding_rules.md       # Copy from rules/coding_rules.md
│   └── PHILOSOPHY.md          # Copy from PHILOSOPHY.md
├── shared/                   # Cross-cutting shared code copied from this repo
│   ├── logging/              # Logging + colored output (if needed)
│   └── shortcuts/            # Keyboard shortcuts (if PySide6 app)
├── shared_tests/             # Generic tests for copied shared modules
│   ├── test_shortcuts_base.py
│   └── test_shortcuts_manager.py
├── AGENTS.md                 # Copy from templates/AGENTS.md, customize
├── CLAUDE.md                 # Symlink → AGENTS.md
├── pyproject.toml            # Copy from templates/pyproject.toml, customize
├── .pre-commit-config.yaml   # Copy from templates/pre-commit-config.yaml
├── .gitignore                # Copy from templates/gitignore
└── .vscode/
    ├── settings.json         # Copy from templates/vscode_settings.json
    └── extensions.json       # Copy from templates/vscode_extensions.json
```

---

## Setup Checklist

1. **Create directory structure:**
   ```
   mkdir -p src/APPNAME tests/unit tests/integration tests/fixtures scripts docs .vscode
   ```

2. **Copy baseline files and directories:**
   - Promote template files into the new project:
     - `templates/pyproject.toml` → `pyproject.toml` (update `[project]` section)
     - `templates/AGENTS.md` → `AGENTS.md` (fill TODO sections)
     - `templates/pre-commit-config.yaml` → `.pre-commit-config.yaml`
     - `templates/gitignore` → `.gitignore`
     - `templates/vscode_settings.json` → `.vscode/settings.json`
     - `templates/vscode_extensions.json` → `.vscode/extensions.json`
    - Copy `shared/` and `shared_tests/` into the new project root if you need the provided building blocks. The template dependency set already covers a full copy; trim unused shared modules and dependencies afterward if you do not need them.
   - Copy `rules/coding_rules.md` → `docs/coding_rules.md`
   - Copy `PHILOSOPHY.md` → `docs/PHILOSOPHY.md`
   - Create symlink: `ln -s AGENTS.md CLAUDE.md`

3. **Trim copied shared modules (if needed):**
   - Keep only the `shared/` and `shared_tests/` subdirectories you actually use
   - `shared/logging/` — colored logging, file rotating logs, CLI output (see `setting-up-logging` skill)
   - `shared/shortcuts/` — keyboard shortcuts for PySide6 apps (see `setting-up-shortcuts` skill)
   - Keep matching generic tests in `shared_tests/` beside the copied shared modules
   - Update import paths after copying if the project package name changes

4. **Create entry points:**
   ```python
   # src/APPNAME/__init__.py
   __version__ = "0.1.0"

   # src/APPNAME/__main__.py
   from __future__ import annotations

   import argparse
   import sys
   from pathlib import Path

   CLI_WORDS = {"config"}  # Top-level CLI entry words for this app

   def parse_gui_request(argv: list[str]) -> tuple[Path | None, bool] | None:
       parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
       parser.add_argument("path", nargs="?")
       parser.add_argument("--debug", action="store_true")

       try:
           ns, unknown = parser.parse_known_args(argv)
       except SystemExit:
           return None

       if unknown:
           return None

       path = Path(ns.path).expanduser() if isinstance(ns.path, str) else None
       return path, bool(ns.debug)

   def main() -> int:
       argv = sys.argv[1:]

       if argv and (argv[0] in {"-h", "--help"} or argv[0] in CLI_WORDS):
           from APPNAME.bootstrap import create_services
           from APPNAME.cli import build_cli_app

           services = create_services(debug=False)
           app = build_cli_app(services)
           app(args=argv, prog_name="APPNAME", standalone_mode=False)
           return 0

       gui_request = parse_gui_request(argv)
       if gui_request is not None:
           from APPNAME.gui import run_gui

           path, debug = gui_request
           return run_gui(path=path, debug=debug)

       from APPNAME.bootstrap import create_services
       from APPNAME.cli import build_cli_app

       services = create_services(debug=False)
       app = build_cli_app(services)
       app(args=argv, prog_name="APPNAME", standalone_mode=False)
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```
   `__main__.py` is the router only. Keep Typer assembly in `APPNAME.cli`, keep GUI startup in `APPNAME.gui`, and avoid `len(sys.argv) > 1` heuristics. The tiny pre-parse only answers “is this a GUI-shaped invocation?” so `APPNAME`, `APPNAME file.txt`, and `APPNAME --debug` can reach the GUI, while `APPNAME -h` and `APPNAME config ...` stay in Typer.

5. **Create initial test:**
   ```python
   # tests/test_main.py
   from APPNAME.__main__ import main

   def test_main_runs(capsys: pytest.CaptureFixture[str]) -> None:
       assert main() == 0
   ```

6. **Initialize environment:**
    ```bash
    git init
    uv sync --all-extras --group dev
   uv run pre-commit install
   uv run poe lint_full
    uv run poe test
    ```

   After setup, keep using project-local commands through `uv` rather than system-installed binaries: `uv run python`, `uv run pytest`, `uv run ruff`, `uv run basedpyright`, `uv run poe`, `uv run pre-commit`.

7. **Verify everything works:**
   - `uv run poe app` runs the application
   - `uv run poe lint_full` passes with 0 errors
   - `uv run poe test` passes

---

## Graceful Shutdown

Design every app to be interruptible without corruption, hanging, or ugly tracebacks. The shutdown strategy depends on what the app does:

```
App type                              → Strategy
─────────────────────────────────────────────────────────────
Simple script/CLI                     → catch KeyboardInterrupt, exit 130
CLI wrapping a quick subtask          → kill process group immediately
CLI wrapping complex tool (vagrant…)  → SIGTERM → wait → SIGKILL
Qt/async app                          → see building-qt-apps skill
```

### Scripts and simple CLIs

```python
# __main__.py
def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        return 130  # 128 + SIGINT(2), Unix convention
```

### Subprocess wrappers

Always pass `start_new_session=True` — creates a process group so you can kill the entire tree, not just the parent.

**Quick subtask (immediate kill):**

```python
import os, signal, subprocess

process = subprocess.Popen(cmd, start_new_session=True)
try:
    process.wait()
except KeyboardInterrupt:
    os.killpg(process.pid, signal.SIGKILL)
```

**Complex tool wrapper (escalation):**

```python
process = subprocess.Popen(cmd, start_new_session=True)
try:
    process.wait()
except KeyboardInterrupt:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
```

**Async subprocess (complex apps using asyncio):**

```python
process = await asyncio.create_subprocess_exec(*cmd, start_new_session=True)
try:
    await process.wait()
except asyncio.CancelledError:
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except TimeoutError:
        process.kill()
    raise
```

---

## Local Bootstrap Script

Write a local helper script if you want to automate the explicit promotion/copy step. Keep it in the repo or paste it into your shell history; do not describe this as a remote curl-piped bootstrap.

```python
# scripts/bootstrap.py
"""Promote local templates into project files, then initialize the dev environment."""

from pathlib import Path
import shutil
import subprocess


def copy_tree(src: Path, dst: Path) -> None:
    if src.exists() and not dst.exists():
        shutil.copytree(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    source_root = Path("../coding_rules_python").resolve()
    project_root = Path.cwd()

    copy_tree(source_root / "shared", project_root / "shared")
    copy_tree(source_root / "shared_tests", project_root / "shared_tests")
    copy_file(source_root / "templates" / "AGENTS.md", project_root / "AGENTS.md")
    copy_file(source_root / "templates" / "pyproject.toml", project_root / "pyproject.toml")
    copy_file(source_root / "templates" / "pre-commit-config.yaml", project_root / ".pre-commit-config.yaml")
    copy_file(source_root / "templates" / "gitignore", project_root / ".gitignore")
    copy_file(source_root / "templates" / "vscode_settings.json", project_root / ".vscode" / "settings.json")
    copy_file(source_root / "templates" / "vscode_extensions.json", project_root / ".vscode" / "extensions.json")
    copy_file(source_root / "rules" / "coding_rules.md", project_root / "docs" / "coding_rules.md")
    copy_file(source_root / "PHILOSOPHY.md", project_root / "docs" / "PHILOSOPHY.md")
    (project_root / "CLAUDE.md").symlink_to("AGENTS.md")

    subprocess.run(["uv", "sync", "--all-extras", "--group", "dev"], check=True)
    subprocess.run(["uv", "run", "pre-commit", "install"], check=True)
    print("Local bootstrap complete.")

if __name__ == "__main__":
    main()
```

---

## Adapt to Tech Stack & Domain

After scaffolding, **adapt everything to the specific project**. The templates are a starting point, not a straitjacket. `docs/PHILOSOPHY.md` is the only ruling constant — everything else bends to fit the project's tech stack, domain, and constraints.

### What to adapt

| Area | How to adapt |
|------|--------------|
| **Directory layout** | Add/remove/rename directories to match the domain. Not every project needs `cli/`, `ui/`, `wrappers/`, `shared/`. A data pipeline might need `pipelines/`, `schemas/`, `extractors/`. A web service might need `routes/`, `middleware/`, `repositories/`. |
| **Dependencies** | Add domain-specific libraries. Remove unused template defaults. Research current best-in-class libraries for the domain (e.g. SQLAlchemy vs raw asyncpg, Pydantic vs attrs). |
| **pyproject.toml** | Adjust ruff rules, pytest markers, basedpyright overrides for the domain. Some domains need relaxed rules (e.g. data science may need broader `type: ignore` for numpy interop). |
| **AGENTS.md** | Fill TODO sections with project-specific architecture, key decisions, domain vocabulary, and workflows. This is the agent's primary orientation document — make it specific. **Skills section:** remove skills the project won't use (e.g. `building-multi-ui-apps` for a pure CLI), add domain-specific skills (e.g. `building-qt-apps`, `setting-up-shortcuts`). |
| **coding_rules.md** | Extend or override rules for the domain. Add domain-specific conventions (e.g. database migration rules, API versioning policy, data validation requirements). |
| **Test structure** | Adjust to match what matters. A CLI tool needs heavy e2e tests. A library needs heavy unit tests. A web service needs API integration tests. |
| **CI/CD** | Add domain-appropriate checks (e.g. migration consistency, API schema validation, container builds). |

### Wrapper enforcement with banned-api

When the project wraps third-party libraries (for typing, platform abstraction, or swappability), enforce wrapper usage via ruff's `flake8-tidy-imports.banned-api` in `pyproject.toml`:

```toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"soundcard".msg = "Use src/wrappers/audio_backend.py instead"
"faster_whisper".msg = "Use src/wrappers/transcriber.py instead"
```

Wrap when a library is **poorly typed** (need typed facade), **platform-specific** (need abstraction layer), or **swappable** (need stable internal API). The template `pyproject.toml` has commented examples — uncomment and customize per project.

Inside the wrapper files themselves, suppress the ban with a per-file ruff ignore: `"src/wrappers/*".msg = ""` in the banned-api config, or use `# noqa: TID251` on individual import lines.

### Research before building

When setting up a project in an unfamiliar domain or with unfamiliar libraries:

1. **Research the domain's conventions** — look up how well-maintained projects in the same space are structured
2. **Check library compatibility** — verify libraries work together and with basedpyright strict mode (some libraries have poor type stubs; plan wrappers early)
3. **Identify domain-specific tooling** — some domains have their own linters, formatters, or validation tools that complement the base toolchain
4. **Check for basedpyright known issues** — some libraries (numpy, pandas, SQLAlchemy) need specific configuration or stub packages to work cleanly in strict mode

### Quick customization checklist

- [ ] Directory layout matches the domain, not the generic template
- [ ] Dependencies are domain-appropriate (researched, not guessed)
- [ ] AGENTS.md describes *this* project, not a generic Python project
- [ ] coding_rules.md has domain-specific additions if needed
- [ ] Test structure reflects what matters most for this project
- [ ] basedpyright config accounts for domain-specific library quirks
