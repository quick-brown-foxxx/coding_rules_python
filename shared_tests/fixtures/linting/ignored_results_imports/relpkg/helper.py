"""Fixture helper for relative Result import."""

from __future__ import annotations

from rusty_results import Ok, Result


def relative_result() -> Result[str, str]:
    return Ok("relative")
