"""Fixture: unfrozen dataclass with bare ignore (no rationale) — should FAIL."""

from dataclasses import dataclass


@dataclass  # lint-ignore[unfrozen-dataclass]
class NoRationale:
    name: str
