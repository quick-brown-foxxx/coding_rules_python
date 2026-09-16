"""Real-process coverage for the captured-subprocess runner.

Exercises the platform layer the unit fakes cannot: real pipe drains, tree-kill
semantics, caller-cancellation cleanup, and stray write ends. Children come from
the flag-driven ``shared_tests/fixtures/tool_stub.py`` — no network. Written
platform-neutral (``sys.executable``, argv lists) so the Windows CI leg runs it
against the Proactor loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Final

import psutil
import pytest

from shared.subprocess import (
    _signal_tree,  # type: ignore[reportPrivateUsage]  # rationale: the dead-pid suppression is the behavior under test
    _StreamCapture,  # type: ignore[reportPrivateUsage]  # rationale: the drain/truncation contract is tested directly
    output_tail,
    run_subprocess_with_capture,
)

_TOOL_STUB: Final = Path(__file__).parent / "fixtures" / "tool_stub.py"
# the stub would outlive every assertion here if a kill or EOF wait broke
_HANG_SECONDS: Final = 8.0
_TIMEOUT_SECONDS: Final = 2.0
# generous bound: real elapsed ≈ timeout + interpreter startup (~0.5s worst case)
_ELAPSED_LIMIT_SECONDS: Final = 6.0
# a grandchild that must outlive the parent for the whole assertion window
_ORPHAN_SECONDS: Final = 8.0


def _stub_argv(*flags: str) -> list[str]:
    return [sys.executable, str(_TOOL_STUB), *flags]


async def _wait_for_pid_file(path: Path, *, timeout_s: float = 5.0) -> int:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if (pid := _read_pid_file(path)) is not None:
            return pid
        await asyncio.sleep(0.02)
    raise AssertionError(f"timed out waiting for pid file {path}")


def _read_pid_file(path: Path) -> int | None:
    if not path.exists():
        return None
    text = path.read_text().strip()
    return int(text) if text else None


async def _wait_for_dead(pid: int, *, timeout_s: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not psutil.pid_exists(pid):
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"pid {pid} still alive after {timeout_s}s")


def _force_kill(pid: int) -> None:
    with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
        psutil.Process(pid).kill()


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
    assert not run.truncated


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


async def test_timeout_kills_grandchild_tree() -> None:
    """Tree kill: the grandchild that inherited the pipes must die with the parent."""
    child_pid_file = _tmp_pid_path("tree-child")
    run = await run_subprocess_with_capture(
        _stub_argv(
            "--spawn-pipe-child",
            str(_ORPHAN_SECONDS),
            "--child-pid-file",
            str(child_pid_file),
            "--sleep",
            str(_HANG_SECONDS),
        ),
        timeout_s=_TIMEOUT_SECONDS,
    )
    assert run.timed_out
    grandchild_pid = await _wait_for_pid_file(child_pid_file)
    await _wait_for_dead(grandchild_pid)


async def test_success_path_does_not_wait_for_pipe_holding_grandchild() -> None:
    """The child exits but its grandchild holds the pipes; the runner must not
    block on EOF for the orphan's whole lifetime."""
    child_pid_file = _tmp_pid_path("success-child")
    started = time.monotonic()
    run = await run_subprocess_with_capture(
        _stub_argv(
            "--stdout",
            "done",
            "--spawn-pipe-child",
            str(_ORPHAN_SECONDS),
            "--child-pid-file",
            str(child_pid_file),
        ),
        timeout_s=_ELAPSED_LIMIT_SECONDS,
    )
    elapsed = time.monotonic() - started
    assert run.returncode == 0
    assert b"done" in run.stdout
    assert elapsed < _ORPHAN_SECONDS / 2
    # the success path deliberately leaves the orphan alone; clean it up ourselves
    _force_kill(await _wait_for_pid_file(child_pid_file))


async def test_caller_cancellation_kills_tree_and_does_not_leak() -> None:
    """A cancelled runner must tear down the child and its grandchildren."""
    parent_pid_file = _tmp_pid_path("cancel-parent")
    child_pid_file = _tmp_pid_path("cancel-child")
    task = asyncio.create_task(
        run_subprocess_with_capture(
            _stub_argv(
                "--pid-file",
                str(parent_pid_file),
                "--spawn-pipe-child",
                str(_ORPHAN_SECONDS),
                "--child-pid-file",
                str(child_pid_file),
                "--sleep",
                str(_HANG_SECONDS),
            ),
            timeout_s=_HANG_SECONDS,
        )
    )
    parent_pid = await _wait_for_pid_file(parent_pid_file)
    grandchild_pid = await _wait_for_pid_file(child_pid_file)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await _wait_for_dead(parent_pid)
    await _wait_for_dead(grandchild_pid)


async def test_signal_tree_after_exit_is_tolerated() -> None:
    """Signalling an already-reaped pid raises in psutil; the helper absorbs it."""
    process = await asyncio.create_subprocess_exec(
        *_stub_argv("--exit-code", "0"),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.wait()  # reaped: a bare psutil.Process(pid).kill() here would raise
    _signal_tree(process.pid, [], force=True)  # must not raise
    assert process.returncode == 0


@pytest.mark.skipif(os.name != "posix", reason="graceful SIGTERM semantics are POSIX-only")
async def test_kill_grace_is_honored_before_force_kill() -> None:
    """A child that ignores SIGTERM gets the full grace window before SIGKILL."""
    started = time.monotonic()
    run = await run_subprocess_with_capture(
        _stub_argv("--ignore-sigterm", "--sleep", str(_HANG_SECONDS)),
        timeout_s=1.0,
        kill_grace_s=1.0,
    )
    elapsed = time.monotonic() - started
    assert run.timed_out
    # ~1s timeout + ~1s grace; must not return instantly (SIGTERM worked despite ignore)
    assert 1.5 <= elapsed < _ELAPSED_LIMIT_SECONDS


async def test_output_cap_truncates_but_still_drains() -> None:
    """The cap bounds buffered bytes without blocking the writer on a full pipe."""
    run = await run_subprocess_with_capture(
        _stub_argv("--huge-output", "200000"),
        timeout_s=_TIMEOUT_SECONDS,
        max_output_bytes=1000,
    )
    assert run.returncode == 0
    assert run.truncated
    assert len(run.stdout) == 1000


async def test_stdin_devnull_does_not_hang_a_reader() -> None:
    """stdin defaults to DEVNULL, so a child that reads stdin sees EOF immediately."""
    run = await run_subprocess_with_capture(
        _stub_argv("--read-stdin"),
        timeout_s=_TIMEOUT_SECONDS,
    )
    assert b"stdin-bytes:0" in run.stdout


async def test_merge_stderr_folds_stderr_into_stdout_in_order() -> None:
    """merge_stderr preserves interleaving; stderr comes back empty."""
    run = await run_subprocess_with_capture(
        _stub_argv("--stdout", "first", "--stderr", "second"),
        timeout_s=_TIMEOUT_SECONDS,
        merge_stderr=True,
    )
    assert run.stderr == b""
    assert run.stdout.index(b"first") < run.stdout.index(b"second")


async def test_capture_preserves_carriage_return_frames() -> None:
    """Raw capture keeps \\r progress frames; consumers normalize them for display."""
    run = await run_subprocess_with_capture(
        _stub_argv("--progress", "--sleep", "0.05"),
        timeout_s=_TIMEOUT_SECONDS,
    )
    assert not run.timed_out
    assert b"\r" in run.stdout


def test_output_tail_normalizes_and_tails() -> None:
    assert output_tail(b"a\rb\rc\n", b"d\n", tail_lines=2) == "c\nd"


def test_output_tail_empty_stream_is_empty() -> None:
    assert output_tail(b"") == ""
    assert output_tail() == ""


async def test_stream_capture_fake_reader_returns_finite_chunks() -> None:
    """The fake-reader contract: finite chunks then b"", never a repeat/spin."""
    reader = _FakeReader([b"ab", b"cdef", b""])
    capture = _StreamCapture(None)
    await capture.drain(reader)
    assert capture.snapshot() == b"abcdef"
    assert not capture.truncated


async def test_stream_capture_caps_and_flags_truncation() -> None:
    reader = _FakeReader([b"ab", b"cdef", b"gh", b""])
    capture = _StreamCapture(4)
    await capture.drain(reader)
    assert capture.snapshot() == b"abcd"
    assert capture.truncated


class _FakeReader:
    """StreamReader stand-in that yields finite chunks and always terminates."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def read(self, n: int) -> bytes:
        await asyncio.sleep(0)  # real reads yield to the loop; a fake must too
        return self._chunks.pop(0)


def _tmp_pid_path(name: str) -> Path:
    return Path(tempfile.gettempdir()) / f"opencode-subprocess-{name}-{os.getpid()}.pid"
