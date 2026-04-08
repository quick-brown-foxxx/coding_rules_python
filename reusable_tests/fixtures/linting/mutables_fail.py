"""Fixture: banned module-level mutable state — should FAIL."""

from __future__ import annotations

# Mutable list
_cache: list[str] = []

# Mutable dict
registry: dict[str, int] = {}  # lint-ignore[raw-dict]: fixture for check_module_mutables testing

# Mutable set
seen = set()

# Constructor calls
items = list()
data = dict()
