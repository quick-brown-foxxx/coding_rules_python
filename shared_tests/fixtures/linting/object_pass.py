"""Fixture: valid object uses — should PASS."""

from __future__ import annotations

from collections.abc import Coroutine
from typing import TypeIs


class MyConfig:
    name: str


# TypeIs guard — allowed
def is_config(obj: object) -> TypeIs[MyConfig]:
    return isinstance(obj, MyConfig)


# Variadic args — allowed
def signal_handler(*_args: object) -> None:
    pass


# Coroutine type param — allowed
async def run_coro(coro: Coroutine[object, None, str]) -> str:
    return await coro


# Normal typed code — no object at all
def process(name: str, count: int) -> str:
    return f"{name}: {count}"
