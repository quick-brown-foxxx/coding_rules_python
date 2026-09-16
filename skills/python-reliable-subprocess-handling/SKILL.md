---
name: python-reliable-subprocess-handling
description: >-
  Notes for advanced subprocess handling in Python for spawning, waiting on, timing out, killing, and capturing output from subprocesses. Load when writing installer, CLI-wrapper, tool-runner, or background-job code that runs child processes, or when debugging "my subprocess timeout didn't work" and "captured output is empty" symptoms. Covers asyncio timeout + cancellation output loss, orphaned children holding pipes open, output tails for logging, and the asyncio subprocess test-double contract.
---

# Python Reliable Subprocess Handling

## Prerequisites

This skill extends myai's `engineering-principles`. Load that first. `writing-python-code` is assumed to be already loaded. Start with `writing-python-code` for the baseline subprocess rules (no `shell=True`, `create_subprocess_exec`, handle `TimeoutError`); this skill covers the traps that only show up once a timeout, a kill, or a process tree is involved.

**Ready-made implementation + tests.** this repo ships a self-contained version of the reference pattern at [`shared/subprocess.py`](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/shared/subprocess.py), with real-process tests at [`shared_tests/test_subprocess_utils.py`](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/shared_tests/test_subprocess_utils.py) and the flag-driven child-process stub they spawn at [`shared_tests/fixtures/tool_stub.py`](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/shared_tests/fixtures/tool_stub.py). Copy them into a project and adapt. The text below explains *why* that code is shaped the way it is, so you can change it on purpose instead of rediscovering the traps.

**Status: working memo, not a guide.** Everything below came from one real debugging session; treat it as field notes. Verify against your runtime before relying on it, and expect corrections — some of this is version-sensitive behavior of asyncio internals, not documented contracts.

## The big trap: `communicate()` loses output when cancelled

`asyncio.subprocess.Process.communicate()` drains both streams into **its own local buffer** while it runs. If you wrap it in `asyncio.timeout(...)` and the timeout fires, the cancellation throws that buffer away. The data is gone:

- it was already consumed from the OS pipe into the coroutine's locals;
- after you `kill()` the process, the pipes hit EOF, so any later `communicate()` / `read()` returns `b""`.

Symptom we hit: "timeout worked, but the recovered output is empty even though the installer had clearly printed progress." Confirmed empirically — do not trust a second `communicate()` after cancellation to recover anything.

**Fix: don't let the drained bytes live inside the cancellable task.** Read in bounded chunks into a holder you own:

```python
import asyncio
from dataclasses import dataclass, field


@dataclass
class StreamCapture:
    """Drains a stream into owned chunks that survive task cancellation."""

    _chunks: list[bytes] = field(default_factory=list)

    async def drain(self, reader: asyncio.StreamReader) -> None:
        while chunk := await reader.read(1 << 16):
            self._chunks.append(chunk)

    def snapshot(self) -> bytes:
        return b"".join(self._chunks)
```

Chunked reads (not one `read()` until EOF) matter for the same reason: every chunk is safely in the holder *before* the next `await`, so a cancel mid-way only loses the one in-flight chunk.

## Second trap: `kill()` is single-PID, and orphans hold pipes open

`process.kill()` terminates only the direct child. If that child spawned its own children (a CLI wrapper around a node/jvm worker, shell scripts, anything), those grandchildren usually inherit stdout/stderr — and **a pipe gets EOF only when every write end is closed**.

Full failure chain we hit:

1. timeout fires, wrapper killed;
2. wrapper's child (a worker binary) survives, still holds the pipe write ends;
3. code awaited the reader tasks to finish → blocked until the orphan finished its entire multi-minute download;
4. the "timed out" log line was placed *after* that await → user saw ~minutes of silence and concluded the timeout was ignored. It wasn't.

Two lessons:

- **Never gate the timeout report behind cleanup.** Log/announce "timed out" immediately; do recovery work after.
- Don't wait for pipe EOF on a killed process tree. Snapshot what you hold and cancel the readers.

Proper tree kill is platform-specific and we deliberately skipped it (revisit if orphaned work ever matters): POSIX `start_new_session=True` + `os.killpg`, Windows Job Objects or `taskkill /T`, or a psutil tree kill (`children(recursive=True)` + kill bottom-up — the one cross-platform option). Cheap partial mitigation: `contextlib.suppress(ProcessLookupError, PermissionError)` around `kill()` — asyncio raises `ProcessLookupError` cross-platform when the process was already reaped, and Windows `TerminateProcess` can surface `PermissionError` (WinError 5) for a dead-but-unreaped child. Both mean "already gone".

`wait()` is well-behaved though: it survives cancellation and is safe to call again after a kill.

## Reference pattern: run, capture, timeout, report

Distilled from working code (an auto-installer that downloads a browser engine). Memo-grade — adjust shapes freely.

```python
import asyncio
import contextlib


def output_tail(*streams: bytes, tail_lines: int = 20) -> str:
    """Last meaningful lines; installer progress bars use \\r, split on those too."""
    text = "\n".join(s.decode(errors="replace").replace("\r", "\n") for s in streams)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-tail_lines:])


async def run_tool_with_capture(argv: list[str], *, timeout_s: float) -> tuple[int | None, bytes, bytes]:
    """Run argv, capture output, enforce a timeout. Never raises for tool failure.

    Returns (returncode, stdout, stderr); returncode is None on timeout.
    """
    captured_out, captured_err = StreamCapture(), StreamCapture()
    readers: list[asyncio.Task[None] | None] = [None, None]
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert process.stdout is not None and process.stderr is not None  # PIPEs above
        readers[0] = asyncio.create_task(captured_out.drain(process.stdout))
        readers[1] = asyncio.create_task(captured_err.drain(process.stderr))
        timed_out = False
        try:
            async with asyncio.timeout(timeout_s):
                await process.wait()
        except TimeoutError:
            timed_out = True
            with contextlib.suppress(ProcessLookupError, PermissionError):
                process.kill()
            await process.wait()
        # success path: wait() returned, but EOF isn't guaranteed yet if the
        # child spawned grandchildren — drain tasks finish on their own EOF;
        # give them a moment only if you must have the full output on success.
        if not timed_out:
            await asyncio.gather(*(t for t in readers if t is not None))
    except Exception:
        for t in readers:
            if t is not None and not t.done():
                t.cancel()
        raise
    if timed_out:
        for t in readers:
            if t is not None and not t.done():
                t.cancel()  # orphan may still hold write ends; don't wait for EOF
    return process.returncode, captured_out.snapshot(), captured_err.snapshot()
```

Notes on choices, so future-you can re-argue them:

- The shipped `shared/subprocess.py` packages this pattern as a frozen `SubprocessRun` result (with a `timed_out` flag) plus a `_kill_and_reap` helper for the kill race — read it before adapting this sketch.
- Cancelled readers on the timeout path: partial output is "output at timeout" and good enough; the alternative is waiting for the orphan.
- If the process may spawn pipe-holding children, even the *success* path's `gather` can hang on EOF — see the orphan section. Worth a bounded wait there if that's your situation.
- Progress bars: `\r`-redrawn bars turn into one giant line. Normalizing `\r` → `\n` before tailing makes the output usable in logs and error messages.

## Surfacing captured output

What worked well as UX, keep or adapt:

- **not stream the installer live**; capture silently.
- on failure: full tail into the WARNING log record; last output line appended to the user-facing message (`"...install failed (fatal: disk full)"`) — that last line is usually the actual reason.
- on success: tail into DEBUG (a durable file log at DEBUG is nice to have).
- on timeout: say "timed out" plus the last captured line, e.g. "downloaded 55%" — it tells the user it was a download problem, not a tool crash.

## Child-side buffering surprise

A piped child's stdout is block-buffered (Python child: several KB). Progress prints can sit in the *child's* userspace buffer, and `kill()` destroys it. When writing your own probe scripts use `print(..., flush=True)`; for third-party children there's nothing to do except expect gaps in captured output. Don't mistake this for the cancellation-loss trap above — different mechanism, similar symptom.

## Testing doubles: honor the reader contract

Two test-double bugs we created and then had to fix — both look like product bugs when they bite:

- **A fake `StreamReader.read()` that always returns the same payload, never `b""`**, combined with a `while chunk := await reader.read(...)` consumer, spins forever — and because a plain coroutine returning without an await point never yields to the loop, it **starves the entire event loop**. The fake must return the payload once, then `b""`.
- **A fake `wait()` that returns without ever yielding** (`async def` but no await point inside) means concurrently-created drain tasks never get a loop tick before the code snapshots the capture. Real processes always yield; fake it with `await asyncio.sleep(0)`.

And a meta-lesson that paid off twice: before trusting asyncio subprocess/cancellation semantics, write a 15-line probe script with `asyncio.timeout` + a sleeping child and *watch* what actually happens. Two of the assumptions above ("second communicate recovers the buffer", "read-after-kill sees buffered bytes") died in 30 seconds when probed.

Doubles cannot cover the platform layer — real pipes, kill semantics, orphan write ends. [`shared_tests/test_subprocess_utils.py`](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/shared_tests/test_subprocess_utils.py) covers that with real processes spawned from the flag-driven [`tool_stub.py`](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/shared_tests/fixtures/tool_stub.py); keep that split (fake the runner in unit tests, spawn real ones for this layer).

## Open questions / not handled yet

- process-tree kill (POSIX killpg / Windows Jobs / psutil) — known gap, see above.
- Windows: covered by the shared real-process tests (the Windows CI leg runs them against the Proactor loop, the default there — never install a Selector event-loop override, or subprocess support breaks). macOS has no CI leg; POSIX semantics assumed identical to Linux. Note the *launch* of downloaded browser engines (not this layer) can additionally hit macOS Gatekeeper for unsigned builds.
- interleaving of stdout+stderr is lost (captured separately); fine for tails.
- live progress streaming to a UI — deliberately not done; capture-only.
- SIGPIPE behavior when we cancel readers and abandon the pipe: the orphan keeps writing into a pipe we stop reading; assumed harmless, unverified.

---

## Related myai Skills

- **`engineering-principles`** — Parent skill. Language-agnostic philosophy: fail fast, error handling as control flow, explicit-over-clever.
- **`writing-python-code`** — Baseline Python rules this skill refines: no `shell=True`, `create_subprocess_exec`, handle `TimeoutError`, cross-platform constraints.
- **`testing-python`** — Where these subprocess doubles fit into the broader pytest/e2e strategy.
- **`systematic-debugging`** (myai) — For the "timeout was ignored" / "output empty" symptoms when the cause is not yet obvious.
