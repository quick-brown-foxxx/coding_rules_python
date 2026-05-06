"""Fixture: dataclasses missing frozen=True — should FAIL."""

from dataclasses import dataclass


@dataclass
class UnfrozenSimple:
    name: str


@dataclass(slots=True)
class UnfrozenWithSlots:
    name: str
    version: str


@dataclass(frozen=False)
class ExplicitlyUnfrozen:
    name: str
