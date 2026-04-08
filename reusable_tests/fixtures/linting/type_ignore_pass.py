"""Fixture: type:ignore with proper error code and rationale — should PASS."""

from __future__ import annotations

import sys

x: int = sys.argv  # type: ignore[assignment]  # argv is untyped in some stubs

# No type:ignore at all — always fine
y: str = "hello"
