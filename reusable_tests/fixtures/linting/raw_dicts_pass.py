"""Fixture: no raw dict annotations in business logic — should PASS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypedDict


class UserData(TypedDict):
    name: str
    age: int


@dataclass(frozen=True, slots=True)
class Config:
    host: str
    port: int


# Final constant dict — allowed
DEFAULTS: Final[dict[str, str]] = {"theme": "dark"}


# Local variable inside function — allowed
def build_cache() -> None:
    cache: dict[str, int] = {}
    _ = cache


# **kwargs — fine
def forward(**kwargs: str) -> None:
    pass


# Normal typed code
def greet(name: str) -> str:
    return f"hello {name}"
