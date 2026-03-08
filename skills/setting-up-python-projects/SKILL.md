---
name: setting-up-python-projects
description: "Bootstrap new Python projects: directory structure, pyproject.toml, pre-commit, uv sync. Use when creating a new project from scratch."
---

# Setting Up Python Projects

New projects start with the full safety net configured. Templates are in the repo: <https://github.com/quick-brown-foxxx/coding_rules_python/tree/master/templates>`.

Make sure to read repo's readme and copy coding rules from `rules/coding_rules.md` to the project `docs/coding_rules.md`.

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
│   └── coding_rules.md       # Copy from rules/coding_rules.md
├── shared/                   # Cross-cutting (logging, shortcuts)
├── AGENTS.md                 # Copy from templates/AGENTS.md, customize
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

2. **Copy template files:**
   - `templates/pyproject.toml` → `pyproject.toml` (update `[project]` section)
   - `templates/AGENTS.md` → `AGENTS.md` (fill TODO sections)
   - `templates/pre-commit-config.yaml` → `.pre-commit-config.yaml`
   - `templates/gitignore` → `.gitignore`
   - `templates/vscode_settings.json` → `.vscode/settings.json`
   - `templates/vscode_extensions.json` → `.vscode/extensions.json`
   - `rules/coding_rules.md` → `docs/coding_rules.md`

3. **Create entry points:**
   ```python
   # src/APPNAME/__init__.py
   __version__ = "0.1.0"

   # src/APPNAME/__main__.py
   import sys

   def main() -> int:
       if len(sys.argv) > 1:
           return cli_main()  # CLI mode
       return gui_main()      # GUI mode (if applicable)

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

---

## Bootstrap Script

```python
# scripts/bootstrap.py
"""Set up development environment."""
import subprocess

def main() -> None:
    subprocess.run(["uv", "sync", "--all-extras", "--group", "dev"], check=True)
    subprocess.run(["uv", "run", "pre-commit", "install"], check=True)
    print("Development environment ready.")

if __name__ == "__main__":
    main()
```

---

## Customization Points

- **Qt app**: uncomment PySide6/qasync in pyproject.toml, add `ui/` directory
- **CLI app**: uncomment typer in pyproject.toml, add `cli/` directory
- **HTTP client**: uncomment httpx in pyproject.toml
- **Wrapper enforcement**: add `[tool.ruff.lint.flake8-tidy-imports.banned-api]` section
