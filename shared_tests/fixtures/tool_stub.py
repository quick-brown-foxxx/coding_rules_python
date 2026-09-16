"""Flag-driven process stub for real-subprocess tests.

Mimics the observable behavior of a tool installer (e.g. ``patchright install
chromium``) without network access: writes payload lines, draws ``\\r``-style
progress-bar frames, optionally spawns a grandchild that inherits the pipe
write ends and outlives the parent, then sleeps and exits with a code.

Flags: --stdout TEXT  --stderr TEXT  --progress  --exit-code N
       --sleep S (hold before exit)  --spawn-pipe-child S (grandchild lifetime)
"""

from __future__ import annotations

import subprocess
import sys
import time

_TOTAL = "184.3 MiB"


def _flag_value(name: str) -> str | None:
    argv = sys.argv[1:]
    return argv[argv.index(name) + 1] if name in argv else None


def _has_flag(name: str) -> bool:
    return name in sys.argv[1:]


def _draw_progress() -> None:
    """Mimic installer progress: one carriage-return-drawn bar, flushed per frame."""
    sys.stdout.write(f"downloading chromium {_TOTAL}\r")
    for frame in ("10%", "55%", "100%"):
        sys.stdout.write(f"{frame} of {_TOTAL}\r")
        sys.stdout.flush()


def main() -> int:
    stdout_text = _flag_value("--stdout")
    stderr_text = _flag_value("--stderr")
    if stdout_text is not None:
        print(stdout_text, flush=True)
    if stderr_text is not None:
        print(stderr_text, file=sys.stderr, flush=True)
    if _has_flag("--progress"):
        _draw_progress()
    grandchild_seconds = _flag_value("--spawn-pipe-child")
    if grandchild_seconds is not None:
        # inherits stdout/stderr: holds the pipe write ends past the parent's death
        subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({grandchild_seconds})"])
    sleep_seconds = _flag_value("--sleep")
    if sleep_seconds is not None:
        time.sleep(float(sleep_seconds))
    exit_code = _flag_value("--exit-code")
    return int(exit_code) if exit_code is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
