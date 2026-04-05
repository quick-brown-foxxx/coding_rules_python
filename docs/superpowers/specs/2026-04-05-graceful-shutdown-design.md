# Graceful Shutdown Architecture — Design Spec

## Problem

No existing coverage of Ctrl+C handling, signal management, or graceful shutdown anywhere in the coding standards. Real issues:

- Qt apps: Ctrl+C doesn't work, works with delay, or breaks the app
- Subprocess-wrapping apps: can't stop if wrapped tool hangs — must kill terminal
- Ugly KeyboardInterrupt tracebacks on Ctrl+C
- Complex async/internal logic needs architectural consideration for interruptibility

## Principle

**Design every app to be interruptible at any point without corruption, hanging, or ugly death.**

This is an architectural concern, not a signal-handling checklist. The shutdown strategy depends on what the app does.

## Decision Tree

```
What does your app do?
├── Simple script/CLI (no long-running children)
│   → Catch KeyboardInterrupt at top level, clean exit, no traceback
│
├── CLI that wraps other tools (subprocess)
│   ├── Simple subtask (quick, non-critical)
│   │   → Kill process group immediately on Ctrl+C
│   └── Complex tooling wrapper (vagrant, docker, builds)
│       → Escalation: SIGTERM → wait N seconds → SIGKILL
│       → Second Ctrl+C kills everything immediately
│
└── Qt/async app
    → Make SIGINT work in Qt event loop
    → Cancel async tasks orderly on shutdown
    → Clean up resources (locks, temp files, connections)
```

## Changes by File

### 1. `setting-up-python-projects/SKILL.md` (+40-50 lines)

New section **"Graceful Shutdown"** after the Setup Checklist. This is the architectural anchor — where the agent learns *which pattern to pick* when scaffolding a new project.

Content:

- The principle (one sentence)
- Decision tree (which strategy based on app type)
- Pattern A — simple script/CLI:

```python
# In __main__.py or script entry point
def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        return 130  # 128 + SIGINT(2), standard Unix convention
```

- Pattern B — subprocess wrapper (simple subtask, immediate kill):

```python
import os
import signal

def run_tool(cmd: list[str]) -> Result[str, str]:
    process = subprocess.Popen(cmd, start_new_session=True)
    try:
        process.wait()
    except KeyboardInterrupt:
        os.killpg(process.pid, signal.SIGKILL)
        return Err("Interrupted")
    return Ok("Done") if process.returncode == 0 else Err(f"Exit {process.returncode}")
```

- Pattern C — subprocess wrapper (complex tool, escalation):

```python
import os
import signal

def run_tool(cmd: list[str], graceful_timeout: float = 5.0) -> Result[str, str]:
    process = subprocess.Popen(cmd, start_new_session=True)
    try:
        process.wait()
    except KeyboardInterrupt:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=graceful_timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
        return Err("Interrupted")
    return Ok("Done") if process.returncode == 0 else Err(f"Exit {process.returncode}")
```

- Pattern D — async subprocess (for complex apps using asyncio):

```python
async def run_tool(cmd: list[str], graceful_timeout: float = 5.0) -> Result[str, str]:
    process = await asyncio.create_subprocess_exec(*cmd, start_new_session=True)
    try:
        await process.wait()
    except asyncio.CancelledError:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=graceful_timeout)
        except TimeoutError:
            process.kill()
        raise
    if process.returncode == 0:
        return Ok("Done")
    return Err(f"Exit {process.returncode}")
```

- Rule: always use `start_new_session=True` (or `process_group=0`) when spawning subprocesses that might hang — this creates a new process group so you can kill the entire tree

### 2. `writing-python-scripts/SKILL.md` (+10-15 lines)

New brief section **"Ctrl+C Handling"** after the CLI Note section.

Content:

- Rule: no KeyboardInterrupt tracebacks in scripts
- Update the script template's entry point to wrap with try/except KeyboardInterrupt
- If script spawns subprocesses: kill on interrupt, don't leave orphans

Updated template entry point:

```python
if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)
```

### 3. `building-qt-apps/SKILL.md` (+15-20 lines)

New section **"Ctrl+C and Shutdown"** after the Key Rules section (or near async integration).

Content:

- The SIGINT problem: Qt's event loop doesn't let Python process signals, so Ctrl+C appears to do nothing
- Fix: `signal.signal(signal.SIGINT, signal.SIG_DFL)` before `loop.run_forever()` — lets the OS handle SIGINT directly (immediate termination, no Python-level handling needed)
- For apps that need cleanup before exit: use a QTimer-based signal check + `QApplication.quit()` instead of SIG_DFL
- Orderly async shutdown: cancel pending tasks, await cleanup, then exit

Updated main() pattern:

```python
import signal

def main() -> int:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Let Ctrl+C terminate the app (Qt blocks Python signal handling by default)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    with loop:
        window = MainWindow()
        window.show()
        loop.run_forever()
    return 0
```

- Note: if the app needs graceful cleanup on Ctrl+C (save state, release locks, stop recordings), use a signal handler that calls `QApplication.quit()` instead of `SIG_DFL`, so Qt's shutdown sequence runs normally

### 4. `rules/coding_rules.md` (+3-5 lines)

Add one rule to the Architecture section:

> **Graceful shutdown:** All apps must handle Ctrl+C without tracebacks or hanging. Scripts: catch `KeyboardInterrupt` at entry point. Subprocess wrappers: kill child process groups on interrupt. Qt apps: install SIGINT handler before event loop. See `setting-up-python-projects` skill for patterns.

## What stays OUT

- **`writing-python-code`** — already over 500-line budget, and this is architectural guidance not code-level style
- **No new standalone skill** — content is inherently contextual, belongs where agents already look per app type
- **No `atexit` patterns** — atexit doesn't run on SIGKILL and is unreliable for the cases we care about

## Key Technical Decisions

1. **`start_new_session=True` always** for subprocesses that might hang — creates process group for clean killing
2. **Exit code 130** for Ctrl+C — Unix convention (128 + signal number 2)
3. **`SIG_DFL` as default Qt fix** — simplest, covers 90% of cases. Graceful cleanup is opt-in when needed
4. **Escalation pattern** (SIGTERM → wait → SIGKILL) only for complex wrappers — simple tools get immediate kill
5. **Async uses `CancelledError`** not `KeyboardInterrupt` — asyncio's cancellation is the right mechanism in async context
