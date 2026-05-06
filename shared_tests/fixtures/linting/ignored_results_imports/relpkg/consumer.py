"""Fixture: ignored relative imported Result call should FAIL."""

from __future__ import annotations

from .helper import relative_result


def run() -> None:
    relative_result()
