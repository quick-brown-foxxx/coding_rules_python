"""Fixture: ignored package re-exported Result call should FAIL."""

from __future__ import annotations

from pkg import reexported_result


def run() -> None:
    reexported_result()
