# Async Patterns Guide

Async rules and integration patterns. See [PHILOSOPHY.md](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/PHILOSOPHY.md) section 8.

---

## When to Use Async

| Use async               | Don't use async           |
| ----------------------- | ------------------------- |
| File I/O                | Pure data transformations |
| Network requests        | Simple calculations       |
| Subprocess execution    | In-memory operations      |
| Operations >100ms       | Quick lookups             |
| Parallel I/O operations | Sequential pure logic     |

---

## Core Patterns

### HTTP Requests

```python
async def fetch_data(url: str) -> Result[bytes, str]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            resp.raise_for_status()
            return Ok(resp.content)
    except httpx.HTTPError as e:
        return Err(f"HTTP error: {e}")
```

### Subprocess Execution

```python
async def run_command(args: list[str]) -> Result[str, str]:
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            return Err(f"Command failed: {stderr.decode()}")
        return Ok(stdout.decode())
    except FileNotFoundError:
        return Err(f"Command not found: {args[0]}")
```

### Concurrent Operations

```python
async def fetch_all(urls: list[str]) -> list[Result[bytes, str]]:
    return await asyncio.gather(*(fetch_data(url) for url in urls))
```

### Timeouts

```python
async def fetch_with_timeout(url: str) -> Result[bytes, str]:
    try:
        async with asyncio.timeout(10):
            return await fetch_data(url)
    except TimeoutError:
        return Err(f"Timeout fetching {url}")
```

---

## Qt + Async Integration

### qasync Setup

```python
import asyncio
import qasync
from PySide6.QtWidgets import QApplication

def main() -> int:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    with loop:
        # ... setup windows ...
        loop.run_forever()
    return 0
```

### QAsyncSignalBridge

Bridge async coroutines to Qt signals:

```python
class QAsyncSignalBridge(QObject):
    finished = Signal(object)
    error = Signal(str)

    def run_async(
        self,
        coro: Coroutine[object, None, T],
        on_success: Callable[[T], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        async def _wrapped() -> None:
            try:
                result = await coro
                if on_success:
                    on_success(result)
                else:
                    self.finished.emit(result)
            except Exception as e:
                if on_error:
                    on_error(str(e))
                else:
                    self.error.emit(str(e))

        loop = asyncio.get_event_loop()
        self._task = loop.create_task(_wrapped())
```

### ThreadPoolExecutor for Blocking Operations

When a library only provides sync API:

```python
class AsyncRecorder(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def start_recording(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._recorder.start)
```

---

## Rules Summary

1. **Never** call `subprocess.run()`, `time.sleep()`, or synchronous HTTP in async context
2. **Never** use `shell=True` in subprocess calls
3. **Always** use `asyncio.create_subprocess_exec()` for subprocesses
4. **Always** use `async with` for resource management (HTTP clients, file handles)
5. **Never** mix sync and async in the same call chain
6. **Always** handle `TimeoutError` for operations that may hang
