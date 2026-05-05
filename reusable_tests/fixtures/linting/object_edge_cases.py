"""Fixture: edge-case object annotations — mixed PASS and FAIL."""

from __future__ import annotations

from collections.abc import Sequence


# *args: object and **kwargs: object — should PASS (variadic exemption)
def accept_anything(*args: object, **kwargs: object) -> None:
    pass


# Sequence[object] in return type — should FAIL
def get_items() -> Sequence[object]:
    return []
