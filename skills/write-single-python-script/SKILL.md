---
name: write-single-python-script
description: Use when creating a single-file Python script, automation tool, or small utility using PEP 722 inline metadata
---

# Write Single Python Script

## Overview

Single-file scripts use PEP 722 inline metadata for dependencies, executed via `uv run --script`. All type safety and error handling rules still apply.

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

# ... TypedDict definitions, Final constants ...

# =============================================================================
# Business Logic
# =============================================================================

# ... pure functions returning Result[T, E] ...

# =============================================================================
# CLI Interface
# =============================================================================

app = typer.Typer(help="Description", add_completion=False)

@app.command()
def main_command() -> None:
    result = do_work()
    if result.is_err:
        typer.echo(f"Error: {result.unwrap_err()}", err=True)
        sys.exit(1)
    typer.echo(result.unwrap())

if __name__ == "__main__":
    app()
```

## Tool Config

Create `pyproject.toml` alongside the script for ruff + basedpyright config only (no `[project]` section needed).

## When to Use Jinja2

When the script produces text output (HTML, markdown, configs):

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader(Path(__file__).parent))
template = env.get_template("template.html")
output = template.render(**data)
```

## When NOT to Use Single Script

- Multiple source files needed -> full project
- Tests needed -> full project
- GUI needed -> full project
- Will grow beyond ~500 lines -> full project

## CLI Note

Use typer for all scripts with `uv`. Use argparse only if the script must work without any external dependencies (stdlib-only, no uv).
