---
name: writing-python-scripts
description: >
  ALWAYS LOAD THIS SKILL WHEN CREATING ANY STANDALONE PYTHON SCRIPT OR SINGLE-FILE AUTOMATION. Do not create Python scripts directly — use this skill first.
  Single-file Python scripts with PEP 723 inline metadata, uv run, and typer CLI.
---

# Writing Python Scripts

Single-file scripts use PEP 723 inline metadata for dependencies, executed via `uv run --script`. All type safety and error handling rules from `writing-python-code` still apply.

---

## When to Use Single Script

| Single Script (PEP 723) | Full Project |
|--------------------------|--------------|
| One task, one file | Multiple features |
| No tests needed | Tests required |
| Templating / generation / automation | Application with UI or API |
| Run directly: `./script.py` | Run via: `uv run poe app` |
| Dependencies in script header | Dependencies in pyproject.toml |
| Under ~500 lines | Will grow beyond ~500 lines |

---

## Layout

```
app/
├── script.py             # Self-contained with inline deps
├── template.html         # Jinja2 templates (if generating text)
├── schema.json           # Validation schema (if validating configs)
├── configs/              # Configuration files (if multiple are needed)
├── pyproject.toml        # Tool config only (ruff, basedpyright)
└── .gitignore
```

---

## Script Template

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "typer>=0.12.0",
#     "rusty-results>=1.1.1",
#     # Add as needed:
#     # "jinja2>=3.1.0",       # For text output generation
#     # "pyyaml>=6.0.0",       # For YAML config loading
#     # "jsonschema>=4.20.0",  # For config validation
# ]
# ///

import sys
from pathlib import Path
from typing import Final, TypedDict, Required

import typer
from rusty_results import Result, Ok, Err

# =============================================================================
# Constants & Types
# =============================================================================

TEMPLATE_PATH: Final[Path] = Path(__file__).parent / "template.html"

class ItemConfig(TypedDict):
    name: Required[str]
    # ...

# =============================================================================
# Business Logic
# =============================================================================

def load_config(path: Path) -> Result[ItemConfig, str]: ...
def process_item(config: ItemConfig) -> Result[str, str]: ...

# =============================================================================
# CLI Interface
# =============================================================================

app = typer.Typer(help="Description", add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})

@app.command()
def main_command() -> None:
    result = do_work()
    if result.is_err:
        typer.echo(f"Error: {result.unwrap_err()}", err=True)
        sys.exit(1)
    typer.echo(result.unwrap())

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)  # No traceback on Ctrl+C
```

---

## Tool Config (pyproject.toml)

No `[project]` section needed — just ruff + basedpyright config:

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

---

## CLI Note

Use typer for all scripts with `uv`. Use argparse only if the script must work without any external dependencies (stdlib-only, no uv).

**Always** pass `context_settings={"help_option_names": ["-h", "--help"]}` to `typer.Typer()` — typer only supports `--help` by default, and users expect `-h` to work.

---

## Ctrl+C Handling

Scripts must not dump tracebacks on Ctrl+C. The template entry point above catches `KeyboardInterrupt` and exits with code 130 (Unix convention: 128 + signal 2).

If a script spawns subprocesses, always use `start_new_session=True` so Ctrl+C can kill the entire process tree. See `setting-up-python-projects` skill for subprocess shutdown patterns.
