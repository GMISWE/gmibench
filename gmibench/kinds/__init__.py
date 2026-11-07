"""Kinds: how a type of task is sent, checked, faked and priced.

A suite names its kind in `suite.yaml` (`kind: coding`). Many suites can share one kind:
`coding` and `coding_hard` are both `coding`. Add a new kind only for a new task shape
(for example long-context retrieval or multi-turn chat): write a subclass of `Kind` in
this package and add it to `KINDS`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import Kind
from .coding import CodingKind
from .documents import DocumentsKind
from .tool_use import ToolUseKind

if TYPE_CHECKING:
    from ..suites import Suite

KINDS: dict[str, Kind] = {k.name: k for k in (CodingKind(), ToolUseKind(), DocumentsKind())}


def get_kind(name: str) -> Kind:
    """Look up a kind by name."""
    try:
        return KINDS[name]
    except KeyError:
        raise ValueError(f"unknown kind '{name}'. Known kinds: {', '.join(KINDS)}") from None


def kind_of(suite: "Suite") -> Kind:
    return get_kind(suite.kind)


__all__ = ["Kind", "KINDS", "get_kind", "kind_of"]
