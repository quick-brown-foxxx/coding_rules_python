"""Fixture: edge-case object annotations — mixed PASS and FAIL."""

from __future__ import annotations

from collections.abc import Coroutine, Sequence


# *args: object and **kwargs: object — should PASS (variadic exemption)
def accept_anything(*args: object, **kwargs: object) -> None:
    pass


# Exact Coroutine[object, None, T] shape — should PASS
async def run_allowed(allowed_coro: Coroutine[object, None, str]) -> str:
    return await allowed_coro


# Sequence[object] in return type — should FAIL
def get_items() -> Sequence[object]:
    return []


# Coroutine[object, int, T] — should FAIL (second arg must be None)
async def run_bad_first(first_coro: Coroutine[object, int, str]) -> None:
    raise RuntimeError(first_coro)


# Coroutine[T, object, U] — should FAIL
async def run_bad_send(send_coro: Coroutine[int, object, str]) -> None:
    raise RuntimeError(send_coro)


# Coroutine[T, None, object] — should FAIL
async def run_bad_return(return_coro: Coroutine[int, None, object]) -> None:
    raise RuntimeError(return_coro)
