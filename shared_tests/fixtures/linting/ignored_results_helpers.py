"""Fixture helper module for ignored_results_imports."""

from __future__ import annotations

from rusty_results import Ok, Result


def imported_result() -> Result[str, str]:
    return Ok("helper")


def imported_alias_result() -> Result[str, str]:
    return Ok("helper alias")
