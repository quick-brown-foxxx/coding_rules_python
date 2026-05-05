"""Fixture: edge-case unfrozen dataclasses — should FAIL."""

import dataclasses


# Fully qualified decorator, no parens
@dataclasses.dataclass
class QualifiedNoParen:
    name: str


# Fully qualified decorator with parens but no frozen
@dataclasses.dataclass(slots=True)
class QualifiedWithSlots:
    name: str
    version: str


# Nested class with dataclass decorator
class Outer:
    @dataclasses.dataclass
    class Inner:
        value: int
