from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from comp.judgment.program import CommitSpec, PublicOutputSpec
from comp.judgment.receipts import PublicOutputReceipt

PublicOutput = dict[str, Any]


@dataclass(frozen=True, slots=True)
class DraftSnapshot:
    draft_id: str
    resolved_bundles: frozenset[str] = frozenset()
    active_hazards: frozenset[str] = frozenset()
    fresh: bool = True
    provenance_edges: int = 0


class PublicOutputBlocked(RuntimeError):
    """Raised when public output lacks receipt authority."""


ProjectionBlocked = PublicOutputBlocked


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
    projection: PublicOutputSpec,
    *,
    receipt: PublicOutputReceipt | None = None,
) -> PublicOutput:
    if receipt is None:
        raise PublicOutputBlocked("Public output requires a public-output receipt.")
    _validate_receipt_authorizes_projection(receipt, projection, field_values)
    return {field: field_values.get(field) for field in projection.output_fields}


def _validate_receipt_authorizes_projection(
    receipt: PublicOutputReceipt,
    projection: PublicOutputSpec,
    field_values: Mapping[str, Any],
) -> None:
    if receipt.projection_id != projection.projection_id:
        raise PublicOutputBlocked(
            "Public-output receipt does not authorize this public output."
        )

    unauthorized_fields = tuple(
        field
        for field in projection.output_fields
        if field not in receipt.authorized_fields
    )
    if unauthorized_fields:
        fields = ", ".join(unauthorized_fields)
        raise PublicOutputBlocked(
            f"Public-output receipt has unauthorized field(s): {fields}."
        )

    if receipt.citations is None:
        raise PublicOutputBlocked(
            "Public output requires a clean public-output receipt."
        )

    citations = receipt.citations
    if (
        citations.governance_status != "commit"
        or not citations.commit_package_complete
        or citations.open_obligation_ids
        or citations.hazard_ids
    ):
        raise PublicOutputBlocked(
            "Public output requires a clean public-output receipt."
        )

    if citations.projection_id != receipt.projection_id:
        raise PublicOutputBlocked("Public-output receipt citation output mismatch.")

    if citations.authorized_fields != receipt.authorized_fields:
        raise PublicOutputBlocked(
            "Public-output receipt citation field scope mismatch."
        )

    _validate_projection_value_commitments(citations, projection, field_values)


def _validate_projection_value_commitments(
    citations,
    projection: PublicOutputSpec,
    field_values: Mapping[str, Any],
) -> None:
    commitments_by_field = {}
    for commitment in citations.projection_value_commitments:
        if commitment.field in commitments_by_field:
            raise PublicOutputBlocked(
                f"Public-output receipt has duplicate value commitment: "
                f"{commitment.field}."
            )
        commitments_by_field[commitment.field] = commitment

    for field in projection.output_fields:
        if field not in field_values:
            raise PublicOutputBlocked(
                f"Public output missing committed value: {field}."
            )
        commitment = commitments_by_field.get(field)
        if commitment is None:
            raise PublicOutputBlocked(
                f"Public-output receipt lacks value commitment for field: {field}."
            )
        try:
            matches = commitment.matches_value(field_values[field])
        except (TypeError, ValueError) as exc:
            raise PublicOutputBlocked(
                f"Public output value commitment cannot be verified: {field}."
            ) from exc
        if not matches:
            raise PublicOutputBlocked(
                f"Public output value commitment mismatch: {field}."
            )


__all__ = [
    "DraftSnapshot",
    "PublicOutput",
    "PublicOutputBlocked",
    "ProjectionBlocked",
    "resolved_required_bundles",
    "blocking_hazards_clear",
    "prov_enough",
    "committable",
    "project_public_row",
]
