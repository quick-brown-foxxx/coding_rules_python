"""Fixture: type:ignore violations — should FAIL."""

from __future__ import annotations

# Missing rationale (has error code but no explanation)
x: int = "hello"  # type: ignore[assignment]

# Bare type:ignore without error code at all
y: int = "world"  # type: ignore

# Missing rationale with spaces
z: int = 42.0  # type:  ignore[arg-type]
