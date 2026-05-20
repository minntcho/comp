from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp.judgment import CommitReceipt, ProjectionSpec
from comp.persistence.ledger import (
    ArtifactIntegrityError,
    InMemoryArtifactStore,
    ProjectionReplayBlocked,
    ReceiptLedgerKey,
    verify_artifact_envelope,
    verify_materialized_public_projection,
)


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    artifact_kind: str

    def __post_init__(self) -> None:
        _require_non_empty("artifact_id", self.artifact_id)
        _require_non_empty("artifact_kind", self.artifact_kind)


@dataclass(frozen=True, slots=True)
class ProjectionReplayReport:
    receipt_key: ReceiptLedgerKey
    projection_id: str
    public_row: dict[str, Any]
    artifact_refs: tuple[ArtifactRef, ...]
    artifact_digests: tuple[tuple[str, str], ...]


def replay_public_projection(
    row: Mapping[str, Any],
    projection: ProjectionSpec,
    *,
    receipt: CommitReceipt,
    artifacts: InMemoryArtifactStore,
) -> ProjectionReplayReport:
    public_row = verify_materialized_public_projection(
        row,
        projection,
        receipt=receipt,
    )
    refs = receipt_artifact_refs(receipt)
    artifact_digests = _verified_artifact_digests(refs, artifacts)
    _verify_projection_value_sources(receipt, artifacts)
    return ProjectionReplayReport(
        receipt_key=ReceiptLedgerKey.from_receipt(receipt),
        projection_id=projection.projection_id,
        public_row=public_row,
        artifact_refs=refs,
        artifact_digests=artifact_digests,
    )


def receipt_artifact_refs(receipt: CommitReceipt) -> tuple[ArtifactRef, ...]:
    citations = receipt.citations
    if citations is None:
        return ()

    refs: list[ArtifactRef] = [
        ArtifactRef(citations.commit_package_id, "commit_package"),
        ArtifactRef(citations.governance_decision_id, "governance_decision"),
    ]
    refs.extend(
        ArtifactRef(commitment.source_id, commitment.source_kind)
        for commitment in citations.projection_value_commitments
    )
    refs.extend(
        ArtifactRef(witness_id, "evidence_witness")
        for witness_id in citations.checked_claim_witness_ids
    )
    refs.extend(
        ArtifactRef(judgment_id, "semantic_judgment")
        for judgment_id in citations.semantic_judgment_ids
    )
    refs.extend(
        ArtifactRef(binding_id, "reference_binding")
        for binding_id in citations.reference_binding_ids
    )
    refs.extend(
        ArtifactRef(derived_claim_id, "derived_claim")
        for derived_claim_id in citations.derived_claim_ids
    )
    refs.extend(
        ArtifactRef(trace_id, "calculation_trace")
        for trace_id in citations.calculation_trace_ids
    )
    refs.extend(
        ArtifactRef(formula_id, "formula")
        for formula_id in citations.formula_ids
    )
    return _unique_refs(refs)


def _verified_artifact_digests(
    refs: tuple[ArtifactRef, ...],
    artifacts: InMemoryArtifactStore,
) -> tuple[tuple[str, str], ...]:
    digests: list[tuple[str, str]] = []
    for ref in refs:
        try:
            envelope = artifacts.get(ref.artifact_id)
        except KeyError as exc:
            raise ProjectionReplayBlocked(
                f"Projection replay missing artifact: {ref.artifact_id}."
            ) from exc
        if envelope.artifact_kind != ref.artifact_kind:
            raise ProjectionReplayBlocked(
                f"Projection replay artifact kind mismatch: {ref.artifact_id}."
            )
        try:
            verify_artifact_envelope(envelope)
        except ArtifactIntegrityError as exc:
            raise ProjectionReplayBlocked(
                f"Projection replay artifact body digest mismatch: {ref.artifact_id}."
            ) from exc
        digests.append((envelope.artifact_id, envelope.body_digest))
    return tuple(digests)


def _verify_projection_value_sources(
    receipt: CommitReceipt,
    artifacts: InMemoryArtifactStore,
) -> None:
    if receipt.citations is None:
        return

    for commitment in receipt.citations.projection_value_commitments:
        try:
            envelope = artifacts.get(commitment.source_id)
        except KeyError as exc:
            raise ProjectionReplayBlocked(
                f"Projection replay missing artifact: {commitment.source_id}."
            ) from exc
        if envelope.artifact_kind != commitment.source_kind:
            raise ProjectionReplayBlocked(
                f"Projection replay artifact kind mismatch: {commitment.source_id}."
            )
        if "value" not in envelope.body:
            raise ProjectionReplayBlocked(
                "Projection replay source artifact lacks committed value: "
                f"{commitment.source_id}."
            )
        try:
            matches = commitment.matches_value(envelope.body["value"])
        except (TypeError, ValueError) as exc:
            raise ProjectionReplayBlocked(
                "Projection replay source artifact value cannot be verified: "
                f"{commitment.source_id}."
            ) from exc
        if not matches:
            raise ProjectionReplayBlocked(
                "Projection replay source artifact value commitment mismatch: "
                f"{commitment.field}."
            )


def _unique_refs(refs: list[ArtifactRef]) -> tuple[ArtifactRef, ...]:
    seen: set[ArtifactRef] = set()
    unique: list[ArtifactRef] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return tuple(unique)


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = [
    "ArtifactRef",
    "ProjectionReplayReport",
    "receipt_artifact_refs",
    "replay_public_projection",
]
