from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from comp.judgment.program import CommitSpec, ProjectionSpec


@dataclass(frozen=True, slots=True)
class DraftSnapshot:
    draft_id: str
    resolved_bundles: frozenset[str] = frozenset()
    active_hazards: frozenset[str] = frozenset()
    fresh: bool = True
    provenance_edges: int = 0


def resolved_required_bundles(snapshot: DraftSnapshot, required_bundles: tuple[str, ...]) -> bool:
    return all(bundle in snapshot.resolved_bundles for bundle in required_bundles)


def blocking_hazards_clear(snapshot: DraftSnapshot, blocking_hazards: tuple[str, ...]) -> bool:
    return snapshot.active_hazards.isdisjoint(blocking_hazards)


def prov_enough(snapshot: DraftSnapshot, min_provenance_edges: int) -> bool:
    return snapshot.provenance_edges >= min_provenance_edges


def committable(snapshot: DraftSnapshot, spec: CommitSpec) -> bool:
    return (
        resolved_required_bundles(snapshot, spec.required_bundles)
        and blocking_hazards_clear(snapshot, spec.blocking_hazards)
        and prov_enough(snapshot, spec.min_provenance_edges)
        and (snapshot.fresh or not spec.require_fresh)
    )


def project_public_row(field_values: Mapping[str, Any], projection: ProjectionSpec) -> dict[str, Any]:
    return {field: field_values.get(field) for field in projection.output_fields}


__all__ = [
    "DraftSnapshot",
    "resolved_required_bundles",
    "blocking_hazards_clear",
    "prov_enough",
    "committable",
    "project_public_row",
]
