"""Fixture: banned module-level mutable state — should FAIL."""

from __future__ import annotations

# Mutable list
_cache: list[str] = []

# Mutable dict
registry: dict[str, int] = {}

# Mutable set
seen = set()

# Constructor calls
items = list()
data = dict()
