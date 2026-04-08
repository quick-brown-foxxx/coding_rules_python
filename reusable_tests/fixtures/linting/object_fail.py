"""Fixture: banned object uses — should FAIL."""

from __future__ import annotations

from typing import Required, TypedDict


# dict[str, object] — banned
def load_data(path: str) -> dict[str, object]:
    return {}


# list[object] — banned
def get_items() -> list[object]:
    return []


# Bare object param (not TypeIs) — banned
def process(data: object) -> str:
    return str(data)


# TypedDict with dict[str, object] — banned
class Response(TypedDict):
    data: Required[dict[str, object]]
