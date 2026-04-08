"""Fixture: raw dict with valid ignore — should PASS."""

from __future__ import annotations


def get_env() -> dict[str, str]:  # lint-ignore[raw-dict]: passthrough to os.environ
    return {}
