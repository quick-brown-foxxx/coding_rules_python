"""Fixture: type:ignore missing rationale but lint-ignored — should PASS."""

from __future__ import annotations

x: int = "hello"  # type: ignore[assignment]  # lint-ignore[type-ignore-rationale]: tested elsewhere
