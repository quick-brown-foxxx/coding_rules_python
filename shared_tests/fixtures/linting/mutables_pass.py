"""Fixture: valid module-level state — should PASS."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

# Final constants — allowed
MAX_RETRIES: Final = 3
ALLOWED_TYPES: Final[tuple[str, ...]] = ("json", "yaml")
CONFIG: Final[dict[str, str]] = {"key": "value"}

# Logger — allowed
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    _type_registry: dict[str, type] = {}


# Inside functions — allowed
def build_cache() -> dict[str, int]:  # lint-ignore[raw-dict]: fixture for check_module_mutables testing
    cache: dict[str, int] = {}
    return cache


# Inside classes — allowed
class Manager:
    items: list[str] = []
