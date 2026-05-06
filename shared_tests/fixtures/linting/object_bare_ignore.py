"""Fixture: banned object use with bare ignore — should FAIL."""

from __future__ import annotations


def process(data: object) -> str:  # lint-ignore[restricted-object]
    return str(data)
