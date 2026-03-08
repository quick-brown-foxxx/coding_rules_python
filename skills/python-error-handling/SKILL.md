---
name: python-error-handling
description: Use when implementing error handling in Python - Result pattern, error boundaries, choosing between Result and exceptions
---

# Python Error Handling

## Overview

Errors are values, not exceptions. Use `Result[T, E]` from `rusty-results` for expected failures. Exceptions mean bugs.

## Decision Table

| Situation | Use |
|-----------|-----|
| File not found, network error, invalid input | `Result[T, E]` |
| User provided bad data | `Result[T, E]` |
| Third-party library raised | Catch at boundary -> `Result[T, E]` |
| Invariant violated (should never happen) | `raise` exception |
| Invalid program state (bug) | `raise` exception |

## Pattern

```python
from rusty_results import Result, Ok, Err

def load_config(path: Path) -> Result[Config, str]:
    if not path.exists():
        return Err(f"Config not found: {path}")
    try:
        data = json.loads(path.read_text())
        return Ok(Config(**data))
    except (json.JSONDecodeError, OSError) as e:
        return Err(f"Failed to load: {e}")
```

## Rules

1. **Early returns** - handle error first, keep success path linear:
   ```python
   result = load_data(path)
   if result.is_err:
       return Err(f"Cannot proceed: {result.unwrap_err()}")
   data = result.unwrap()
   ```

2. **Three error boundaries:**
   - Library: catch third-party exceptions -> Result
   - Component: each subsystem returns Result to caller
   - Global: UI/CLI top-level catches everything, shows user message

3. **Never swallow errors** - no `except: pass`, no ignored Results

4. **Cleanup on failure** - if multi-step operation fails midway, clean up partial state

5. **Custom error types** for complex domains:
   ```python
   @dataclass
   class ConfigError:
       path: Path
       reason: str
       line: int | None = None
   ```

## CLI Error Boundary

```python
def main() -> int:
    result = run_app()
    if result.is_err:
        typer.echo(f"Error: {result.unwrap_err()}", err=True)
        return 1
    return 0
```
