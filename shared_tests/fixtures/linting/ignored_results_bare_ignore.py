"""Fixture: bare ignored-result lint ignore should FAIL."""

from __future__ import annotations

from rusty_results import Ok, Result


def load_config() -> Result[str, str]:
    return Ok("config")


def run() -> None:
    load_config()  # lint-ignore[ignored-result]
