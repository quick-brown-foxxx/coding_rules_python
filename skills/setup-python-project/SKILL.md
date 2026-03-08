---
name: setup-python-project
description: Use when creating a new Python project from scratch - sets up directory structure, tooling, and configuration files
---

# Setup Python Project

## Overview

New projects start with the full safety net configured. Templates are at `~/Projects/docs/dev/python_coding/templates/`.

## Setup Checklist

1. **Create directory structure:**
   ```
   mkdir -p src/APPNAME tests/unit tests/integration tests/fixtures scripts docs .vscode
   ```

2. **Copy template files:**
   - `templates/pyproject.toml` -> `pyproject.toml` (update `[project]` section)
   - `templates/AGENTS.md` -> `AGENTS.md` (fill TODO sections)
   - `templates/pre-commit-config.yaml` -> `.pre-commit-config.yaml`
   - `templates/gitignore` -> `.gitignore`
   - `templates/vscode_settings.json` -> `.vscode/settings.json`
   - `templates/vscode_extensions.json` -> `.vscode/extensions.json`
   - `rules/coding_rules.md` -> `docs/coding_rules.md`

3. **Create entry points:**
   ```python
   # src/APPNAME/__init__.py
   __version__ = "0.1.0"

   # src/APPNAME/__main__.py
   import sys

   def main() -> int:
       print("Hello from APPNAME!")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

4. **Create initial test:**
   ```python
   # tests/test_main.py
   from APPNAME.__main__ import main

   def test_main_runs(capsys: pytest.CaptureFixture[str]) -> None:
       assert main() == 0
   ```

5. **Initialize environment:**
   ```bash
   git init
   uv sync --all-extras --group dev
   uv run pre-commit install
   uv run poe lint_full
   uv run poe test
   ```

6. **Verify everything works:**
   - `uv run poe app` runs the application
   - `uv run poe lint_full` passes with 0 errors
   - `uv run poe test` passes

## Customization Points

- **Qt app**: uncomment PySide6/qasync in pyproject.toml, add `ui/` directory
- **CLI app**: uncomment typer in pyproject.toml, add `cli/` directory
- **HTTP client**: uncomment httpx in pyproject.toml
- **Wrapper enforcement**: add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` section

## Reference

See `guides/project-layout.md` for detailed layout documentation.
