from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SelectionReceipt:
    bundle_id: str
    frontier_ids: tuple[str, ...]
    winner_id: str | None
    bundle_version: int
    reason: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    draft_id: str
    winner_receipt_ids: tuple[str, ...]
    barrier_snapshot: tuple[tuple[str, Any], ...]
    public_row_id: str


__all__ = ["SelectionReceipt", "CommitReceipt"]
