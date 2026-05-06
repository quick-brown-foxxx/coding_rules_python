"""Fixture: unfrozen dataclass with valid ignore — should PASS."""

from dataclasses import dataclass


@dataclass(slots=True)  # lint-ignore[unfrozen-dataclass]: builder pattern needs mutation
class Builder:
    name: str
    items: list[str]
