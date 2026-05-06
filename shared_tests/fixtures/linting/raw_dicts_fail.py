"""Fixture: raw dict annotations in domain/business code — should FAIL."""

from __future__ import annotations


# dict param — should use TypedDict/dataclass
def process_user(user: dict[str, str]) -> None:
    pass


# dict return — should use TypedDict/dataclass
def load_config() -> dict[str, int]:
    return {}


# dict class attribute
class Service:
    cache: dict[str, list[str]]


# dict module-level annotation (not Final)
settings: dict[str, str] = {}
