"""Fixture: edge-case module-level mutables — should partially FAIL."""

from __future__ import annotations

import collections
import typing
from typing import TYPE_CHECKING

# Qualified defaultdict at module level — should FAIL
_index = collections.defaultdict(list)

# Qualified OrderedDict at module level — should FAIL
_ordered = collections.OrderedDict()

# typing.Final with a mutable — should PASS (Final exemption)
REGISTRY: typing.Final = {"key": "value"}

if TYPE_CHECKING:
    _type_only_registry: dict[str, str] = {}
else:
    _runtime_registry = {}
