"""Fixture: type:ignore with bare lint-ignore (no rationale) — should FAIL."""

from __future__ import annotations

x: int = "hello"  # type: ignore[assignment]  # lint-ignore[type-ignore-rationale]
