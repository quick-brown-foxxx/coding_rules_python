"""Fixture implementation module exporting Result-returning helpers."""

from __future__ import annotations

from rusty_results import Ok, Result


def reexported_result() -> Result[str, str]:
    return Ok("reexported")
