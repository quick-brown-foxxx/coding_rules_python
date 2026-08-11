---
name: setting-up-logging
description: >
  ALWAYS LOAD THIS SKILL WHEN ADDING LOGGING, CONFIGURING LOG OUTPUT, OR SETTING UP COLORLOG IN PYTHON. Do not configure Python logging directly — use this skill first.
  Set up colored logging and stdout output for Python apps and CLI tools using colorlog.
---

# Setting Up Logging

## Prerequisites

This skill extends myai's `engineering-principles`. Load that first. `using-my-skills` and `engineering-principles` are assumed already loaded via myai bootstrap.

For the general logging philosophy, see myai's `engineering-principles`. This skill covers only Python-specific logging setup: colorlog configuration, file/stdout/stderr logging modes, CLI user output helpers, and QML log routing for PySide6 apps.

Rotating file logging, colored console logging, and colored non-log output. Uses `colorlog` for prefix-only coloring (log prefix is colored, message text stays default). Includes `silence_noisy_loggers()` for pinning noisy third-party loggers at WARNING.

Copy `shared/logging/`.

---

## Key Principle

**File logging is always on** — it's the durable record for post-mortem debugging. Stdout is lost on terminal close; file logs survive.

**Console logging** is for modes where no human reads stdout directly. When you launch a GUI app from terminal or run a server in a container, stdout logs are useful — they show real-time output during development and serve as container log transport (Docker/systemd capture stdout).

**CLI tools must NOT use stdout logging** — stdout is the user interface. Log lines mixed into stdout corrupt the output (imagine `mytool | grep something` with log lines). Use `write_info`/`write_error` for user-facing messages instead. A CLI tool that wants live logs during manual runs mirrors them to **stderr** (`setup_stdout_logging(stream=sys.stderr)`) behind a flag — stdout stays clean.

| Mode | File log | Console log | Non-log colored output |
|------|----------|-------------|------------------------|
| **CLI tool** | Always | Optional on **stderr** (never stdout) | `write_info`, `write_error` for user messages |
| **GUI app** | Always | Yes (stdout, dev convenience from terminal) | No (no terminal) |
| **Server (FastAPI)** | Always | Yes (stdout, container log transport) | No |

---

## When to Use

- **Every app** — `setup_file_logging()` in your entrypoint
- **GUI apps / servers** — also `setup_stdout_logging()` (stdout is not the user interface)
- **CLI tools** — `write_info`/`write_error` for user-facing messages (NOT stdout logging); optionally `setup_stdout_logging(stream=sys.stderr)` for live logs behind a flag
- **Suppressing noisy loggers** — `silence_noisy_loggers()` (curated list, edit `_NOISY_LOGGERS` for your app) or `configure_logger_level("httpx", logging.WARNING)`

---

## Typical Patterns

### CLI tool — file logging + colored user output

```python
import logging
from pathlib import Path
from shared.logging import setup_file_logging, configure_logger_level, write_info, write_error

# File logs always on
setup_file_logging(
    log_dir=Path("~/.local/state/myapp/logs").expanduser(),
    app_name="myapp",
    level=logging.INFO
)
silence_noisy_loggers()

# User-facing output via write_info/write_error (NOT stdout logging)
write_info("Processing 42 items...")
write_error("Connection failed")
```

### CLI tool — with optional live logs on stderr (`--log-level` / `--log-stderr`)

A CLI tool that wants live logs during manual runs wires a typer callback: file log always on at a selectable level, and `--log-stderr` mirrors the same level to a colored **stderr** console — stdout stays the user interface.

```python
import logging
import sys
from pathlib import Path
from typing import Final

import typer

from shared.logging import setup_file_logging, setup_stdout_logging, silence_noisy_loggers

app = typer.Typer(add_completion=False, help="myapp CLI")

_LOG_LEVELS: Final = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


@app.callback()
def _cli_logging(
    log_stderr: bool = typer.Option(
        False, "--log-stderr",
        help="Print colored logs to stderr (stdout stays the user interface)",
    ),
    log_level: str = typer.Option(
        "info", "--log-level",
        help="Log level: debug|info|warning|error (debug captures request/response detail)",
    ),
) -> None:
    """Wire logging for every invocation: file log always, console on demand."""
    level = _LOG_LEVELS.get(log_level.lower())
    if level is None:
        raise typer.BadParameter(f"Unknown --log-level {log_level!r}; use one of: debug, info, warning, error")
    setup_file_logging(log_dir=Path("~/.local/state/myapp/logs").expanduser(), app_name="myapp", level=level)
    silence_noisy_loggers()
    if log_stderr:
        setup_stdout_logging(level=level, stream=sys.stderr)
```

### GUI app / server — file logging + stdout logging

```python
import logging
from pathlib import Path
from shared.logging import setup_file_logging, setup_stdout_logging, silence_noisy_loggers

# File logs always on
setup_file_logging(
    log_dir=Path("~/.local/state/myapp/logs").expanduser(),
    app_name="myapp",
    level=logging.INFO
)
# Stdout logs for dev convenience (visible when launched from terminal / in containers)
setup_stdout_logging(level=logging.INFO)
silence_noisy_loggers()
```

**Stdout output format (colored):**
```
<green>2025-12-19 00:01:35 [INFO] myapp.core:</green> Processing 42 items
<yellow>2025-12-19 00:01:36 [WARNING] myapp.core:</yellow> Slow response from API
```

**File output format (plain):**
```
2025-12-19 00:01:35 [INFO] myapp.core: Processing 42 items
2025-12-19 00:01:36 [WARNING] myapp.core: Slow response from API
```

**Color scheme (stdout only):**

| Level | Color |
|-------|-------|
| DEBUG | Cyan |
| INFO | Green |
| WARNING | Yellow |
| ERROR | Red |
| CRITICAL | Red on white |

---

## Non-Log Colored Output

For CLI tools — colored messages that are NOT log entries (status messages, results, prompts). This is how CLI tools communicate with the user instead of stdout logging:

```python
from shared.logging import write_info, write_success, write_warning, write_error

write_info("Starting download...")      # Green → stdout
write_success("Download complete!")     # Green → stdout
write_warning("Large file detected")   # Yellow → stdout
write_error("Failed to connect")       # Red → stderr
```

---

## Dependencies

```toml
[project]
dependencies = [
    "colorlog>=6.10.1",
]
```

---

## Files to Copy

Use the top-level `shared/logging/` directory in the new project:
- `__init__.py` — public API re-exports
- `logger_setup.py` — `setup_stdout_logging()`, `setup_file_logging()`, `configure_logger_level()`, `silence_noisy_loggers()`
- `non_log_stdout_output.py` — `write_info()`, `write_success()`, `write_warning()`, `write_error()`
- `README.md` — references this skill

Import from it directly: `from shared.logging import ...`.

---

## QML Log Routing (PySide6)

QML `console.info/warn/error` can be routed through Python's `logging` module via a custom Qt message handler. This integrates QML output with your file and stdout logging setup. The handler logs under the `qt.qml` logger name, so you can filter it independently.

See the `building-qt-apps` skill for the full handler implementation and the `console.log()` gotcha (it's silently dropped by Qt).

---

## API Reference

### `setup_file_logging(log_dir, app_name="app", level=INFO, max_bytes=5MB, backup_count=3)`
Add RotatingFileHandler to root logger. Creates `<log_dir>/<app_name>.log`. Always use this — every app needs durable file logs. Default level is INFO; pass `level=logging.DEBUG` to capture everything (e.g. AI request/response diagnostics).

### `setup_stdout_logging(level=logging.INFO, *, stream=None)`
Add colored StreamHandler to root logger. For GUI apps and servers where stdout is not the user interface — streams to stdout by default. Do NOT use for CLI tools; a CLI tool that wants live logs passes `stream=sys.stderr` so stdout stays the user interface.

### `configure_logger_level(logger_name, level, propagate=True)`
Set a specific logger's level. Use to suppress or re-enable individual loggers (e.g. `configure_logger_level("httpx", logging.DEBUG)` to debug one SDK).

### `silence_noisy_loggers()`
Pin curated noisy third-party loggers (HTTP/AI/SQL: `httpx`, `httpcore`, `urllib3`, `openai`, `anthropic`, `aiosqlite`) at WARNING. Call after `setup_*_logging` in the entry point. Edit `_NOISY_LOGGERS` in `logger_setup.py` for your app's dependencies.

### `write_info(message)` / `write_success(message)`
Green text to stdout.

### `write_warning(message)`
Yellow text to stdout.

### `write_error(message)`
Red text to stderr.

---

## Related myai Skills

- **`engineering-principles`** — Parent skill. Language-agnostic philosophy.
- **`building-qt-apps`** — For QML log routing integration with PySide6 apps.
- **`writing-python-code`** — Python-specific coding rules for logger usage in application code.
- **`setting-up-python-projects`** — For including `shared/logging/` in new project bootstrap.
