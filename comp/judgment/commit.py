from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from comp.judgment.program import CommitSpec, ProjectionSpec
from comp.judgment.receipts import CommitReceipt


@dataclass(frozen=True, slots=True)
class DraftSnapshot:
    draft_id: str
    resolved_bundles: frozenset[str] = frozenset()
    active_hazards: frozenset[str] = frozenset()
    fresh: bool = True
    provenance_edges: int = 0


class ProjectionBlocked(RuntimeError):
    """Raised when public projection lacks receipt authority."""


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


def project_public_row(
    field_values: Mapping[str, Any],
    projection: ProjectionSpec,
    *,
    receipt: CommitReceipt | None = None,
) -> dict[str, Any]:
    if receipt is None:
        raise ProjectionBlocked("Public projection requires a CommitReceipt.")
    _validate_receipt_authorizes_projection(receipt, projection)
    return {field: field_values.get(field) for field in projection.output_fields}


def _validate_receipt_authorizes_projection(
    receipt: CommitReceipt,
    projection: ProjectionSpec,
) -> None:
    if receipt.projection_id != projection.projection_id:
        raise ProjectionBlocked(
            "CommitReceipt does not authorize this projection."
        )

    unauthorized_fields = tuple(
        field
        for field in projection.output_fields
        if field not in receipt.authorized_fields
    )
    if unauthorized_fields:
        fields = ", ".join(unauthorized_fields)
        raise ProjectionBlocked(f"CommitReceipt has unauthorized field(s): {fields}.")

    if receipt.citations is None:
        raise ProjectionBlocked("Public projection requires a clean commit receipt.")

    citations = receipt.citations
    if (
        citations.governance_status != "commit"
        or not citations.commit_package_complete
        or citations.open_obligation_ids
        or citations.hazard_ids
    ):
        raise ProjectionBlocked("Public projection requires a clean commit receipt.")

    if citations.projection_id != receipt.projection_id:
        raise ProjectionBlocked("CommitReceipt citation projection mismatch.")

    if citations.authorized_fields != receipt.authorized_fields:
        raise ProjectionBlocked("CommitReceipt citation field scope mismatch.")


__all__ = [
    "DraftSnapshot",
    "ProjectionBlocked",
    "resolved_required_bundles",
    "blocking_hazards_clear",
    "prov_enough",
    "committable",
    "project_public_row",
]
