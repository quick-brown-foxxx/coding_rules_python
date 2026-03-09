---
name: setting-up-logging
description: "Set up colored logging and stdout output for Python apps and CLI tools using colorlog."
---

# Setting Up Logging

Colored logging and stdout output setup for CLI tools, scripts, and applications. Uses `colorlog` for prefix-only coloring (log prefix is colored, message text stays default). Includes rotating file logging for GUI apps and servers.

Copy reusable code from `coding_rules_python/reusable/logging/`.

---

## When to Use

- **CLI tools** — stdout logging only (colored) + `write_info`/`write_error` for non-log output
- **GUI apps / servers** — file logging always on, stdout logging typically off (stdout reserved for user-facing output)
- **Development / debugging** — both stdout and file logging
- **Suppressing noisy loggers** — `configure_logger_level("httpx", logging.WARNING)`

---

## Typical Patterns

### CLI tools — stdout only

```python
import logging
from shared.logging import setup_stdout_logging, configure_logger_level

setup_stdout_logging(level=logging.INFO)
configure_logger_level("httpx", logging.WARNING)
```

### GUI apps / servers — file logging, no stdout

```python
import logging
from pathlib import Path
from shared.logging import setup_file_logging, configure_logger_level

# File logs always running (DEBUG captures everything)
setup_file_logging(
    log_dir=Path("~/.local/state/myapp/logs").expanduser(),
    app_name="myapp",
)
configure_logger_level("httpx", logging.WARNING)
```

### Development — both

```python
import logging
from pathlib import Path
from shared.logging import setup_stdout_logging, setup_file_logging, configure_logger_level

setup_stdout_logging(level=logging.DEBUG)
setup_file_logging(log_dir=Path("logs"), app_name="myapp")
configure_logger_level("httpx", logging.WARNING)
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

For colored messages that are NOT log entries (status messages, results, prompts):

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

Copy the entire `coding_rules_python/reusable/logging/` directory into your project's `shared/logging/`:
- `__init__.py` — public API re-exports
- `logger_setup.py` — `setup_stdout_logging()`, `setup_file_logging()`, `configure_logger_level()`
- `non_log_stdout_output.py` — `write_info()`, `write_success()`, `write_warning()`, `write_error()`
- `README.md` — references this skill

Update import paths after copying (e.g., `from shared.logging import ...`).

---

## API Reference

### `setup_stdout_logging(level=logging.INFO)`
Add colored StreamHandler to root logger. For CLI tools and scripts.

### `setup_file_logging(log_dir, app_name="app", level=DEBUG, max_bytes=5MB, backup_count=3)`
Add RotatingFileHandler to root logger. Creates `<log_dir>/<app_name>.log`. For GUI apps and servers where file logs always run.

### `configure_logger_level(logger_name, level, propagate=True)`
Set a specific logger's level. Use to suppress verbose third-party loggers.

### `write_info(message)` / `write_success(message)`
Green text to stdout.

### `write_warning(message)`
Yellow text to stdout.

### `write_error(message)`
Red text to stderr.
