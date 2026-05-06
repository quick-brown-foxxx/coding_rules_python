"""Fixture: edge-case type:ignore with multiple error codes — should FAIL and PASS."""

from __future__ import annotations

# Multiple error codes WITHOUT rationale — should FAIL
x: int = "hello"  # type: ignore[assignment, arg-type]

# Multiple error codes WITH rationale — should PASS
y: int = "world"  # type: ignore[assignment, arg-type]  # legacy untyped module
