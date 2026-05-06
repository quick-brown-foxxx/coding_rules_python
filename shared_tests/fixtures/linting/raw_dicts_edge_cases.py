"""Fixture: edge-case raw dict annotations — should FAIL."""

from __future__ import annotations


# Nested raw dict — should FAIL
def get_nested() -> dict[str, dict[str, int]]:
    return {}


# dict in a union type — should FAIL
def maybe_dict(value: str | dict[str, int]) -> None:
    pass
