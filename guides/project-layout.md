# Project Layout Guide

When to use which project structure. See [PHILOSOPHY.md](../PHILOSOPHY.md) section 9.

---

## Decision: Single Script vs Full Project

| Single Script (PEP 722)              | Full Project                   |
| ------------------------------------ | ------------------------------ |
| One task, one file                   | Multiple features              |
| No tests needed                      | Tests required                 |
| Templating / generation / automation | Application with UI or API     |
| Run directly: `./script.py`          | Run via: `uv run poe app`      |
| Dependencies in script header        | Dependencies in pyproject.toml |

---

## Single Script Layout (PEP 722)

```
app/
├── script.py             # Self-contained with inline deps
├── template.html         # Jinja2 templates (if generating text)
├── schema.json           # Validation schema (if validating configs)
├── configs/              # Configuration files (if multiple are needed)
├── pyproject.toml        # Tool config only (ruff, basedpyright)
└── .gitignore
```

### Script Header

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.12.0",
#     "jinja2>=3.1.0",
#     "pyyaml>=6.0.0",
#     "rusty-results>=1.1.1",
# ]
# ///
```

### pyproject.toml (Tool Config Only)

```toml
[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "strict"
reportAny = "error"

[tool.ruff]
line-length = 120
target-version = "py314"

[tool.ruff.lint]
extend-select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "RUF"]
ignore = ["S101", "B008", "RUF001"]
```

### Script Internal Structure

Even in a single file, separate concerns with clear sections:

```python
#!/usr/bin/env -S uv run --script
# /// script
# ...
# ///

import ...

# =============================================================================
# Constants & Types
# =============================================================================

TEMPLATE_PATH: Final[Path] = Path(__file__).parent / "template.html"

class ItemConfig(TypedDict):
    name: Required[str]
    ...

# =============================================================================
# Business Logic
# =============================================================================

def load_config(path: Path) -> Result[ItemConfig, str]: ...
def process_item(config: ItemConfig) -> Result[str, str]: ...

# =============================================================================
# CLI Interface
# =============================================================================

app = typer.Typer(help="...")

@app.command()
def generate(...) -> None: ...

if __name__ == "__main__":
    app()
```

---

## Full Project Layout

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
├── pyproject.toml             # Copy from templates/pyproject.toml, customize
├── .pre-commit-config.yaml    # Copy from templates/pre-commit-config.yaml
├── .gitignore                 # Copy from templates/gitignore
└── .vscode/
    ├── settings.json          # Copy from templates/vscode_settings.json
    └── extensions.json        # Copy from templates/vscode_extensions.json
```

### Entry Point Pattern

```python
# src/appname/__main__.py
import sys

def main() -> int:
    if len(sys.argv) > 1:
        return cli_main()  # CLI mode
    return gui_main()      # GUI mode (if applicable)

if __name__ == "__main__":
    sys.exit(main())
```

### Bootstrap Script

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
