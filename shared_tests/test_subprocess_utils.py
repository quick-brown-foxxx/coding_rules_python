"""Real-process coverage for the captured-subprocess runner.

Exercises the platform layer the unit fakes cannot: real pipe drains, kill
semantics, and orphan write-end handling on the timeout path. Children come
from the flag-driven ``shared_tests/fixtures/tool_stub.py`` — no network.
Written platform-neutral (``sys.executable``, argv lists) so the Windows CI leg
runs it against the Proactor loop.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Final

from shared.subprocess import (
    _kill_and_reap,  # type: ignore[reportPrivateUsage]  # rationale: the race suppression is the behavior under test; the helper has no other consumer
    run_subprocess_with_capture,
)

_TOOL_STUB: Final = Path(__file__).parent / "fixtures" / "tool_stub.py"
# the stub would outlive every assertion here if a kill or EOF wait broke
_HANG_SECONDS: Final = 8.0
_TIMEOUT_SECONDS: Final = 2.0
# generous bound: real elapsed ≈ timeout + interpreter startup (~0.5s worst case)
_ELAPSED_LIMIT_SECONDS: Final = 6.0


def _stub_argv(*flags: str) -> list[str]:
    return [sys.executable, str(_TOOL_STUB), *flags]


async def test_run_captures_streams_and_exit_code() -> None:
    """Both streams land byte-exact (modulo OS newline translation) with the exit code."""
    run = await run_subprocess_with_capture(
        _stub_argv("--stdout", "out line", "--stderr", "err line", "--exit-code", "3", "--sleep", "0.05"),
        timeout_s=_TIMEOUT_SECONDS,
    )
    assert run.returncode == 3
    assert run.stdout.strip() == b"out line"
    assert run.stderr.strip() == b"err line"
    assert not run.timed_out


async def test_timeout_kills_child_and_returns_partial_output() -> None:
    """Timeout kills the child; output captured before the kill is still reported."""
    started = time.monotonic()
    run = await run_subprocess_with_capture(
        _stub_argv("--progress", "--sleep", str(_HANG_SECONDS)),
        timeout_s=_TIMEOUT_SECONDS,
    )
    elapsed = time.monotonic() - started
    assert run.timed_out
    assert b"100% of 184.3 MiB" in run.stdout
    # fails if anyone re-adds an EOF wait after the kill
    assert elapsed < _ELAPSED_LIMIT_SECONDS


async def test_timeout_returns_despite_grandchild_holding_pipe() -> None:
    """The orphan-trap regression guard: a grandchild inherits the pipe write
    ends, so awaiting EOF after the kill would hang until it finishes."""
    started = time.monotonic()
    run = await run_subprocess_with_capture(
        _stub_argv("--progress", "--spawn-pipe-child", "5", "--sleep", str(_HANG_SECONDS)),
        timeout_s=_TIMEOUT_SECONDS,
    )
    elapsed = time.monotonic() - started
    assert run.timed_out
    assert b"100% of 184.3 MiB" in run.stdout
    assert elapsed < _ELAPSED_LIMIT_SECONDS


async def test_kill_after_exit_is_tolerated() -> None:
    """Killing an already-reaped process raises; the reap helper absorbs the race."""
    process = await asyncio.create_subprocess_exec(
        *_stub_argv("--exit-code", "0"),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.wait()  # reaped: a bare kill() here would raise ProcessLookupError
    await _kill_and_reap(process)  # must not raise (Windows may surface PermissionError)
    assert process.returncode == 0


async def test_capture_preserves_carriage_return_frames() -> None:
    """Raw capture keeps \\r progress frames; consumers normalize them for display."""
    run = await run_subprocess_with_capture(
        _stub_argv("--progress", "--sleep", "0.05"),
        timeout_s=_TIMEOUT_SECONDS,
    )
    assert not run.timed_out
    assert b"\r" in run.stdout
