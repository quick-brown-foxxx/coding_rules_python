---
name: working-with-qt
description: Use when building or modifying PySide6 Qt desktop applications - covers signals, async integration, manager pattern, wrappers
---

# Working with Qt

## Overview

Qt apps use PySide6 with qasync for async integration. Architecture follows Manager -> Service -> Wrapper layering. Never block the event loop.

## Key Rules

1. **PySide6** (LGPL, no system deps) over PyQt
2. **Never block event loop**: no `subprocess.run()`, no `time.sleep()`, no sync HTTP
3. **qasync** bridges asyncio and Qt event loops
4. **ThreadPoolExecutor** wraps blocking third-party APIs
5. **Typed wrappers** around untyped libraries, enforced via ruff `banned-api`
6. **Signals at class level**, not in `__init__`
7. **camelCase for Qt event handlers** (ignore ruff N802), **snake_case for our slots**

## Architecture

```
UI (MainWindow, Dialogs, TrayIcon)
    |  signals/slots
Manager (coordinates, emits signals)
    |  async via QAsyncSignalBridge
Service (async operations)
    |  typed interface
Wrapper (typed third-party access)
    |
Third-party Library
```

## Quick Patterns

**Async operation from Qt:**
```python
self._bridge.run_async(
    self._service.do_work(data),
    on_success=self._on_success,
    on_error=self._on_error,
)
```

**Blocking lib in async context:**
```python
result = await loop.run_in_executor(self._executor, self._sync_method)
```

**Signal definition:**
```python
class MyManager(QObject):
    work_completed = Signal(str)
    work_failed = Signal(str)
```

## Reference

See `guides/qt-patterns.md` for full patterns including QAsyncSignalBridge implementation, system tray, keyboard shortcuts, lock manager, and testing with pytest-qt.
