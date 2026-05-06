"""Fixture: all dataclasses have frozen=True — should PASS."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleProfile:
    name: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class DetailedProfile:
    name: str
    version: str
    active: bool = True


# Not a dataclass — should be ignored
class RegularClass:
    pass
