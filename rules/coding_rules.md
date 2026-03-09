# Coding Rules

Universal Python coding standards.
Inherits from [PHILOSOPHY.md](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/PHILOSOPHY.md).

For full guide, see [rules navigation doc](https://github.com/quick-brown-foxxx/coding_rules_python/README.md).

---

## 1. Type System

### 1.1 Strict Mode (Non-Negotiable)

basedpyright in strict mode with `reportAny=error`. Every function has type annotations.
No exceptions to strictness.

### 1.2 Banned Patterns

| Banned                             | Use Instead                                            |
| ---------------------------------- | ------------------------------------------------------ |
| `Any`                              | `object` for top type, `Protocol` for duck typing      |
| `typing.cast()`                    | `isinstance`, `TypeIs`, pattern matching               |
| `# type: ignore` without rationale | `# type: ignore[specific-code]  # rationale: <reason>` |
| Raw `dict` in business logic       | `msgspec.Struct`, `dataclass`, or `TypedDict`          |
| Implicit return types              | Explicit annotation on every function                  |

### 1.3 Type Patterns

**External data (JSON, configs, APIs)** → `msgspec.Struct`:

```python
import msgspec

class UserConfig(msgspec.Struct):
    name: str
    port: int
    debug: bool = False

# JSON → typed object (validates at decode time)
config = msgspec.json.decode(raw_bytes, type=UserConfig)

# Dict/YAML → typed object
config = msgspec.convert(raw_dict, type=UserConfig)
```

`TypedDict` is still valid when you need dict compatibility (e.g., `**unpacking`, APIs expecting dicts).

**Domain objects:**

```python
from dataclasses import dataclass

@dataclass(slots=True)
class Profile:
    name: str
    version: str
    active: bool = True
```

**Duck typing:**

```python
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...
```

**Type narrowing (preferred over assumptions):**

```python
from typing import TypeIs

def is_valid_config(obj: object) -> TypeIs[UserConfig]:
    return isinstance(obj, dict) and "name" in obj and "port" in obj
```

**Pattern matching for structural checks:**

```python
match response:
    case {"status": "ok", "data": data}:
        return Ok(data)
    case {"status": "error", "message": msg}:
        return Err(str(msg))
    case _:
        return Err("Unknown response format")
```

### 1.4 Third-Party Library Boundaries

Libraries with weak typing get typed wrappers. Enforce via ruff `banned-api`:

```toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"some_untyped_lib" = { msg = "Use src/wrappers/some_wrapper instead" }
```

When wrappers are impractical, use type stubs in `src/stubs/`.

### 1.5 Constants

```python
from typing import Final

MAX_RETRIES: Final = 3
CONFIG_PATH: Final[Path] = Path("~/.config/app")
```

---

## 2. Error Handling

### 2.1 The Result Pattern

Use `rusty-results` library. Errors are return values, not exceptions.

```python
from rusty_results import Result, Ok, Err

def load_config(path: Path) -> Result[Config, str]:
    if not path.exists():
        return Err(f"Config not found: {path}")
    try:
        data = json.loads(path.read_text())
        return Ok(Config(**data))
    except (json.JSONDecodeError, OSError) as e:
        return Err(f"Failed to load config: {e}")
```

### 2.2 When to Use What

| Situation                                                 | Approach                            |
| --------------------------------------------------------- | ----------------------------------- |
| Expected failure (IO, network, user input, missing file)  | `Result[T, E]`                      |
| Programming error (invariant violation, impossible state) | `raise Exception` (fail-fast)       |
| Third-party library exception                             | Catch at boundary, wrap in `Result` |

### 2.3 Error Handling Rules

- **Early returns.** Handle error path first, keep success path linear:

  ```python
  result = load_data(path)
  if result.is_err:
      return Err(f"Cannot proceed: {result.unwrap_err()}")
  data = result.unwrap()
  # ... success path continues unindented
  ```

- **Custom error types** for complex domains (use dataclasses, not just strings)
- **Never swallow errors.** No `except Exception: pass`. No ignoring Result errors.
- **Cleanup on failure.** If a multi-step operation fails midway, clean up partial state.

### 2.4 Error Boundaries

Three tiers:
1. **Library boundary**: catch third-party exceptions, convert to Result
2. **Component boundary**: each subsystem handles its own errors, returns Result to caller
3. **Global boundary**: UI/CLI top-level catches all remaining errors, shows user-friendly message

```python
# CLI error boundary
def main() -> int:
    result = run_app()
    if result.is_err:
        typer.echo(f"Error: {result.unwrap_err()}", err=True)
        return 1
    return 0
```

---

## 3. Code Style

### 3.1 Formatting

| Rule         | Value                                                |
| ------------ | ---------------------------------------------------- |
| Line length  | 120                                                  |
| Indentation  | 4 spaces                                             |
| Quotes       | Double quotes (single only to avoid escaping)        |
| Import order | stdlib -> third-party -> local (auto-sorted by ruff) |

### 3.2 Naming

| Element                       | Convention                  | Example                        |
| ----------------------------- | --------------------------- | ------------------------------ |
| Modules, functions, variables | `snake_case`                | `load_config`, `user_name`     |
| Classes, TypedDicts           | `PascalCase`                | `ProfileManager`, `UserConfig` |
| Constants                     | `UPPER_SNAKE`               | `MAX_RETRIES`, `DEFAULT_PORT`  |
| Private                       | `_prefix`                   | `_internal_state`              |
| Qt event handlers             | `camelCase` (Qt convention) | `mousePressEvent`              |

### 3.3 Documentation

Google-style docstrings for all public functions and classes:

```python
def create_profile(name: str, version: str) -> Result[Profile, str]:
    """Create a new profile with validation.

    Args:
        name: Profile display name (must be unique)
        version: Telegram Desktop version string

    Returns:
        Ok(Profile) on success, Err with description on failure
    """
```

Comments explain **why**, not **what**. If code needs a comment explaining what it does, the code should be clearer.

---

## 4. Async

### 4.1 When to Use

- All I/O operations (file, network, subprocess)
- Operations taking >100ms
- Concurrent operations that benefit from parallelism
- Do NOT use for simple data transformations or pure functions

### 4.2 Rules

- **Never block the event loop**: no `subprocess.run()`, no `time.sleep()`, no synchronous HTTP
- **Subprocesses**: `asyncio.create_subprocess_exec()` (never `shell=True`)
- **Concurrency**: `asyncio.gather()` for parallel operations
- **Timeouts**: `asyncio.timeout()` for operations that may hang
- **Never mix sync and async** in the same call chain
- **Qt integration**: use `qasync` + `ThreadPoolExecutor` for blocking ops

```python
async def fetch_data(url: str) -> Result[bytes, str]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            return Ok(resp.content)
    except httpx.NetworkError as e:
        return Err(f"Network error: {e}")
```

---

## 5. Preconditions & Validation

Validate early. Fail fast. Don't let invalid state propagate.

### 5.1 Entry Point Validation

At the entry of each subsystem, check:
- Required permissions and access rights
- Required external dependencies (binaries, libraries)
- Configuration validity
- Input sanity (types already guaranteed by type system, but value ranges and business rules need runtime checks)

> **Note:** `msgspec` handles structural validation (types, required fields) at decode time. Precondition checks are still needed for business rules and value ranges.

### 5.2 Pattern

```python
def process_file(path: Path, config: Config) -> Result[Output, str]:
    # Preconditions
    if not path.exists():
        return Err(f"File not found: {path}")
    if not path.suffix == ".yaml":
        return Err(f"Expected .yaml file, got: {path.suffix}")
    if config.max_size and path.stat().st_size > config.max_size:
        return Err(f"File too large: {path.stat().st_size} > {config.max_size}")

    # Validated — proceed with business logic
    ...
```

---

## 6. Architecture

### 6.1 Layered Dependencies

```
Presentation (Qt GUI / CLI / API)
        |  (consumes, never imported by lower layers)
        v
Domain (Managers, Models, Business Rules)
        |  (pure logic, UI-agnostic)
        v
Utilities (Helpers, Wrappers, Common)
```

- Dependencies flow **downward only**
- UI is a **plugin** — adding CLI, GUI, or API should not change business logic
- Domain layer never imports from presentation

### 6.2 Data vs Logic Separation

| Concern                      | Implementation                         |
| ---------------------------- | -------------------------------------- |
| Data carriers                | `dataclass`, `TypedDict`, `NamedTuple` |
| Business logic               | Manager/Service classes                |
| Stateless operations         | Pure functions in utils                |
| Lifecycle & state management | Stateful classes with explicit state   |

### 6.3 Scale-Appropriate

- **Single script**: functions and clear sections within one file
- **Small project**: few modules, flat structure
- **Large project**: `src/` layout with `core/`, `ui/`, `cli/`, `utils/`, `wrappers/`

---

## 7. Security

- **No `shell=True`** in subprocess calls. Construct argument lists explicitly.
- **Validate paths** before operations (especially user-provided paths)
- **No hardcoded secrets.** Use environment variables or dotenv.
- **Input validation** at system boundaries (user input, API requests, file contents)
- **Subprocess argument validation**: never interpolate user input into commands

---

## 8. Performance

- Clear code first, optimize only with profiling data
- `__slots__` on frequently instantiated dataclasses
- Batch I/O operations (don't read files one by one in a loop)
- Lazy loading for expensive resources (load on first use, not import time)
- Concurrent I/O with `asyncio.gather()`

---

## 9. Git Conventions

### 9.1 Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

### 9.2 Pre-Commit Checklist

Before committing:
1. `uv run poe lint_full` passes (type check + lint + format)
2. Tests pass
3. New code has tests (where appropriate)
4. Public APIs have docstrings
5. No hardcoded secrets or debug prints
6. Commit message follows convention
