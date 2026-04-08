"""Fixture: banned object use with valid ignore — should PASS."""

from __future__ import annotations


def log_value(label: str, value: object) -> None:  # lint-ignore[restricted-object]: accepts any
    print(f"{label}: {value}")
