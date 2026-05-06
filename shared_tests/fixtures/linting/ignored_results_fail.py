"""Fixture: ignored Result-returning calls should FAIL."""

from __future__ import annotations

from rusty_results import Err, Ok, Result


def load_config() -> Result[str, str]:
    return Ok("config")


def save_config() -> rusty_results.Result[None, str]:  # type: ignore[name-defined]  # fixture: qualified name is syntactic only
    return Err("not implemented")


def run() -> None:
    load_config()
    save_config()
