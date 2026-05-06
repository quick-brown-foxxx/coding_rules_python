"""Fixture: mutable state with valid ignore — should PASS."""

from __future__ import annotations

_plugin_registry: dict[str, str] = {}  # lint-ignore[module-mutable-state]: needed  # lint-ignore[raw-dict]: fixture
