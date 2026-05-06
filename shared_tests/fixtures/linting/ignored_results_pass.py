"""Fixture: handled Result-returning calls should PASS."""

from __future__ import annotations

from rusty_results import Ok, Result


def load_config() -> Result[str, str]:
    return Ok("config")


def notify() -> None:
    return None


def assigned() -> None:
    result = load_config()
    if result.is_err:
        return


def propagated() -> Result[str, str]:
    return load_config()


def non_result_call() -> None:
    notify()


def intentionally_ignored() -> None:
    load_config()  # lint-ignore[ignored-result]: fire-and-forget probe in fixture
