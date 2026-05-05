"""Fixture: edge-case module-level mutables — should partially FAIL."""

from __future__ import annotations

import collections
import typing

# Qualified defaultdict at module level — should FAIL
_index = collections.defaultdict(list)

# Qualified OrderedDict at module level — should FAIL
_ordered = collections.OrderedDict()

# typing.Final with a mutable — should PASS (Final exemption)
REGISTRY: typing.Final = {"key": "value"}
