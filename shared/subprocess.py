"""Cross-platform subprocess runner with cancellation-safe output capture.

Self-contained asyncio runner: drain both streams into owned buffers, enforce a
timeout, and return the output captured so far even when the child is killed.
See the `python-reliable-subprocess-handling` skill for the traps this shape
avoids (cancellable `communicate()` output loss, orphaned grandchildren holding
pipe write ends open).
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

_CHUNK_BYTES: Final = 1 << 16


@dataclass(frozen=True, slots=True)
class SubprocessRun:
    """Outcome of one captured tool run; a failed tool is data, a failed spawn raises."""

    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool


class _StreamCapture:
    """Drains one stream into owned chunks that survive task cancellation.

    Every chunk lands in the holder before the next ``await``, so cancelling
    the drain task mid-stream loses at most the one in-flight chunk.
    """

    def __init__(self) -> None:
        self._chunks: list[bytes] = []

    async def drain(self, reader: asyncio.StreamReader) -> None:
        while chunk := await reader.read(_CHUNK_BYTES):
            self._chunks.append(chunk)

    def snapshot(self) -> bytes:
        return b"".join(self._chunks)


async def _kill_and_reap(process: asyncio.subprocess.Process) -> None:
    """Kill the direct child and reap it, tolerating the already-exited race.

    asyncio raises ``ProcessLookupError`` (cross-platform) when the process was
    already reaped; Windows ``TerminateProcess`` can surface ``PermissionError``
    (WinError 5) for a dead-but-unreaped child. Both mean "already gone".
    """
    with contextlib.suppress(ProcessLookupError, PermissionError):
        process.kill()
    await process.wait()


async def run_subprocess_with_capture(argv: Sequence[str], *, timeout_s: float) -> SubprocessRun:
    """Run ``argv``, capture both streams, enforce a timeout. Never raises for tool failure.

    Spawn problems (missing executable, hostile environment) raise — those are
    environment/programming errors; a tool that runs and then fails (exit code,
    timeout) is a value.

    Timeout semantics: the direct child is killed and reaped, the output
    captured so far is returned with ``timed_out=True``, and the drain readers
    are cancelled without waiting for pipe EOF — a surviving grandchild keeps
    the write ends open and would block that wait until it finishes.

    # ponytail: kill() is wrapper-only — a grandchild may outlive it; upgrade
    # to a process-group kill (POSIX start_new_session + killpg, Windows Job
    # Objects/taskkill, or a psutil tree kill) if orphaned workers ever matter.
    """
    captured_out, captured_err = _StreamCapture(), _StreamCapture()
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert process.stdout is not None  # PIPEs passed above
    assert process.stderr is not None
    readers = (
        asyncio.create_task(captured_out.drain(process.stdout)),
        asyncio.create_task(captured_err.drain(process.stderr)),
    )
    try:
        async with asyncio.timeout(timeout_s):
            await process.wait()
    except TimeoutError:
        await _kill_and_reap(process)
        # Snapshot what we hold and stop draining: an orphaned grandchild may
        # keep the pipe write ends open, so awaiting the readers could block
        # until the orphan's whole job finishes.
        for reader in readers:
            reader.cancel()
        assert process.returncode is not None  # reaped by _kill_and_reap
        return SubprocessRun(
            returncode=process.returncode,
            stdout=captured_out.snapshot(),
            stderr=captured_err.snapshot(),
            timed_out=True,
        )
    # wait() returned, but EOF is not guaranteed when the child spawned
    # pipe-holding children of its own: the gather assumes none do (add a
    # bounded wait here if that ever becomes real).
    await asyncio.gather(*readers)
    assert process.returncode is not None  # reaped by wait()
    return SubprocessRun(
        returncode=process.returncode,
        stdout=captured_out.snapshot(),
        stderr=captured_err.snapshot(),
        timed_out=False,
    )
