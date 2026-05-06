"""Fixture: handled imported Result-returning calls should PASS."""

from __future__ import annotations

from ignored_results_helpers import imported_alias_result as renamed_result
from ignored_results_helpers import imported_result
import ignored_results_helpers as helpers_alias


def run() -> None:
    direct_result = imported_result()
    alias_result = renamed_result()
    module_result = helpers_alias.imported_result()

    if direct_result.is_err or alias_result.is_err or module_result.is_err:
        return

    imported_result()  # lint-ignore[ignored-result]: explicit fire-and-forget probe in fixture
