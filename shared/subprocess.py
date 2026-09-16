"""Cross-platform subprocess runner with cancellation-safe output capture.

Self-contained asyncio runner: drain both streams into owned buffers, enforce a
timeout, kill the whole process tree, and return the output captured so far
even when the child is killed. See the
`python-reliable-subprocess-handling` skill for the traps this shape avoids.

Behaviors covered (all verified by real-process tests in
``shared_tests/test_subprocess_utils.py``):

- ``communicate()`` under cancellation loses drained bytes — we read into owned
  chunk holders instead.
- ``Process.kill()`` is single-PID — a grandchild that inherited the pipe write
  ends keeps the pipes open. We kill the whole tree with ``psutil`` (a ppid walk,
  so it works the same on Windows) and bound every wait for pipe EOF.
- A caller cancelling the runner must not leak the child, the readers, or the
  pipe transports. Every failure path funnels through ``_abort``.
- A noisy child must not OOM us: ``max_output_bytes`` caps what is buffered
  while still draining the pipe so the child never blocks on a full pipe.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Protocol

import psutil

_CHUNK_BYTES: Final = 1 << 16
# After the child is dead (or reaped), buffered pipe bytes flush near-instantly.
# Only a pipe-holding orphan keeps a write end open, so bound the wait instead
# of blocking cleanup on it.
_SETTLE_GRACE_S: Final = 1.0


@dataclass(frozen=True, slots=True)
class SubprocessRun:
    """Outcome of one captured tool run; a failed tool is data, a failed spawn raises."""

    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool
    truncated: bool = False


class _AsyncByteReader(Protocol):
    """Minimal read surface of ``asyncio.StreamReader``; lets tests inject a fake."""

    async def read(self, n: int) -> bytes: ...


class _StreamCapture:
    """Drains one stream into owned chunks that survive task cancellation.

    Every chunk lands in the holder before the next ``await``, so cancelling the
    drain task mid-stream loses at most the one in-flight chunk. When
    ``max_bytes`` is set the reader keeps draining to EOF (so the child never
    blocks on a full pipe) but only the first ``max_bytes`` are buffered.
    """

    def __init__(self, max_bytes: int | None) -> None:
        self._chunks: list[bytes] = []
        self._max_bytes = max_bytes
        self._stored = 0
        self._truncated = False

    async def drain(self, reader: _AsyncByteReader) -> None:
        while chunk := await reader.read(_CHUNK_BYTES):
            remaining = self._remaining()
            if remaining is None or remaining >= len(chunk):
                self._chunks.append(chunk)
                self._stored += len(chunk)
            elif remaining > 0:
                self._chunks.append(chunk[:remaining])
                self._stored += remaining
                self._truncated = True
            else:
                self._truncated = True

    def _remaining(self) -> int | None:
        return None if self._max_bytes is None else self._max_bytes - self._stored

    def snapshot(self) -> bytes:
        return b"".join(self._chunks)

    @property
    def truncated(self) -> bool:
        return self._truncated


def _tree_pids(pid: int) -> list[int]:
    """Snapshot the descendant pids; a dead or inaccessible process has none."""
    with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return [child.pid for child in psutil.Process(pid).children(recursive=True)]
    return []


def _signal_pid(pid: int, *, force: bool) -> None:
    """Terminate (SIGTERM) or kill (SIGKILL) one pid, tolerating a dead one."""
    with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        target = psutil.Process(pid)
        target.kill() if force else target.terminate()


def _signal_tree(pid: int, descendants: Sequence[int], *, force: bool) -> None:
    """Signal the parent first (so it cannot respawn), then the snapshot children."""
    _signal_pid(pid, force=force)
    for child_pid in descendants:
        _signal_pid(child_pid, force=force)


async def _kill_tree(process: asyncio.subprocess.Process, *, kill_grace_s: float) -> None:
    """Kill the tree, optionally allowing a graceful window first, then reap.

    The descendant list is snapshotted once and reused for both passes: after a
    soft SIGTERM reaps the parent, its surviving children are reparented and
    can no longer be found by walking down from the parent pid.
    """
    if process.returncode is not None:
        return
    descendants = _tree_pids(process.pid)
    if kill_grace_s > 0:
        _signal_tree(process.pid, descendants, force=False)
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(kill_grace_s):
                await process.wait()
    _signal_tree(process.pid, descendants, force=True)
    with contextlib.suppress(ProcessLookupError, PermissionError):
        process.kill()  # guarantee the direct child dies even if psutil could not signal it
    await process.wait()


async def _settle_readers(readers: Sequence[asyncio.Task[None]]) -> bool:
    """Wait briefly for pipe EOF, then cancel the stragglers.

    Returns whether any reader had to be cancelled — i.e. a pipe-holding orphan
    survived the kill, so the pipe transports must be closed explicitly.
    """
    _, pending = await asyncio.wait(readers, timeout=_SETTLE_GRACE_S)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    return bool(pending)


def _close_pipes(process: asyncio.subprocess.Process) -> None:
    """Release the pipe transports when a cancelled drain never reached EOF.

    ``Process`` exposes no public pipe-close; without this the transports
    linger until GC (``unclosed transport`` warnings, Proactor closed-pipe noise
    on Windows).
    """
    with contextlib.suppress(Exception):
        process._transport.close()  # type: ignore[reportPrivateUsage]  # rationale: no public API releases the subprocess pipe transports


async def _abort(
    process: asyncio.subprocess.Process,
    readers: Sequence[asyncio.Task[None]],
    *,
    kill_grace_s: float,
) -> None:
    """Best-effort teardown after an unexpected failure (caller cancel et al.)."""
    with contextlib.suppress(Exception):
        await _kill_tree(process, kill_grace_s=kill_grace_s)
    for task in readers:
        task.cancel()
    await asyncio.gather(*readers, return_exceptions=True)
    _close_pipes(process)


async def run_subprocess_with_capture(
    argv: Sequence[str],
    *,
    timeout_s: float,
    kill_grace_s: float = 0.0,
    max_output_bytes: int | None = None,
    merge_stderr: bool = False,
) -> SubprocessRun:
    """Run ``argv``, capture streams, enforce a timeout. Never raises for tool failure.

    Spawn problems (missing executable, hostile environment) raise — those are
    environment/programming errors; a tool that runs and then fails (exit code,
    timeout) is a value. A caller cancellation, by contrast, is propagated after
    the tree is torn down.

    Args:
        argv: program and arguments; never shell-interpolated.
        timeout_s: wall-clock budget before the tree is killed.
        kill_grace_s: seconds to allow a graceful terminate before the forced tree
            kill. On Windows ``terminate`` is abrupt anyway (no SIGTERM), so the
            window only delays on POSIX. 0 kills at once.
        max_output_bytes: per-stream cap; the pipe is still drained, but only the
            first N bytes are buffered and ``truncated`` is set.
        merge_stderr: fold stderr into stdout (preserves ordering); returned
            ``stderr`` is then empty.

    Returns:
        The exit code, both captured streams, and timeout/truncation flags.
    """
    stderr_target = asyncio.subprocess.STDOUT if merge_stderr else asyncio.subprocess.PIPE
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=stderr_target,
    )
    assert process.stdout is not None  # PIPEs passed above
    captured_out = _StreamCapture(max_output_bytes)
    captured_err = _StreamCapture(max_output_bytes)
    readers: list[asyncio.Task[None]] = [asyncio.create_task(captured_out.drain(process.stdout))]
    if process.stderr is not None:  # None when merged into stdout
        readers.append(asyncio.create_task(captured_err.drain(process.stderr)))
    timed_out = False
    try:
        try:
            async with asyncio.timeout(timeout_s):
                await process.wait()
        except TimeoutError:
            timed_out = True
            await _kill_tree(process, kill_grace_s=kill_grace_s)
        # Success or timeout: bound the EOF wait. wait() returning is not EOF
        # when the child spawned pipe-holding grandchildren.
        if await _settle_readers(readers):
            _close_pipes(process)
    except BaseException:
        # Caller cancelled or an unexpected error: never leak the tree/readers.
        await _abort(process, readers, kill_grace_s=kill_grace_s)
        raise
    assert process.returncode is not None  # wait() or _kill_tree reaped it
    return SubprocessRun(
        returncode=process.returncode,
        stdout=captured_out.snapshot(),
        stderr=captured_err.snapshot(),
        timed_out=timed_out,
        truncated=captured_out.truncated or captured_err.truncated,
    )


def output_tail(*streams: bytes, tail_lines: int = 20) -> str:
    """Last meaningful lines across streams; ``\\r`` progress bars are split too.

    Installer progress bars redraw with ``\\r``, which turns into one giant line
    unless normalized before tailing.
    """
    text = "\n".join(stream.decode(errors="replace").replace("\r", "\n") for stream in streams)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-tail_lines:])
