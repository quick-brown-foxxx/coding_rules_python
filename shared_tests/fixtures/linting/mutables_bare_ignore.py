"""Fixture: mutable state with bare ignore — should FAIL."""

from __future__ import annotations

_cache: list[str] = []  # lint-ignore[module-mutable-state]
