"""Fixture: ignored imported Result-returning calls should FAIL."""

from __future__ import annotations

from rusty_results import Ok, Result as R

from ignored_results_helpers import imported_alias_result as renamed_result
from ignored_results_helpers import imported_result
import ignored_results_helpers
import ignored_results_helpers as helpers_alias


def local_result() -> R[str, str]:
    return Ok("local")


def run() -> None:
    local_result()
    imported_result()
    renamed_result()
    ignored_results_helpers.imported_result()
    helpers_alias.imported_result()
    helpers_alias.imported_alias_result()
