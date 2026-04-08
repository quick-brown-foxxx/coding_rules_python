"""Fixture: raw dict with bare ignore (no rationale) — should FAIL."""

from __future__ import annotations


def get_env() -> dict[str, str]:  # lint-ignore[raw-dict]
    return {}
