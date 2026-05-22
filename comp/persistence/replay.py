from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp.judgment import PublicOutputReceipt, PublicOutputSpec
from comp.judgment.receipts import DependencyFingerprint
from comp.persistence.ledger import (
    ArtifactIntegrityError,
    ArtifactStore,
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
    dependency_fingerprints: tuple[DependencyFingerprint, ...] = ()


def replay_public_projection(
    row: Mapping[str, Any],
    projection: PublicOutputSpec,
    *,
    receipt: PublicOutputReceipt,
    artifacts: ArtifactStore,
) -> ProjectionReplayReport:
    public_row = verify_materialized_public_projection(
        row,
        projection,
        receipt=receipt,
    )
    refs = receipt_artifact_refs(receipt)
    artifact_digests = _verified_artifact_digests(refs, artifacts)
    _verify_projection_value_sources(receipt, artifacts)
    _verify_dependency_fingerprint_sources(receipt, artifacts)
    _verify_source_evidence_span_fingerprints(receipt, artifacts)
    _verify_reference_catalog_snapshot_coverage(receipt, artifacts)
    return ProjectionReplayReport(
        receipt_key=ReceiptLedgerKey.from_receipt(receipt),
        projection_id=projection.projection_id,
        public_row=public_row,
        artifact_refs=refs,
        artifact_digests=artifact_digests,
        dependency_fingerprints=_dependency_fingerprints(receipt),
    )


def receipt_artifact_refs(receipt: PublicOutputReceipt) -> tuple[ArtifactRef, ...]:
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
    refs.extend(
        ArtifactRef(fingerprint.dependency_id, fingerprint.dependency_kind)
        for fingerprint in citations.dependency_fingerprints
    )
    return _unique_refs(refs)


def _verified_artifact_digests(
    refs: tuple[ArtifactRef, ...],
    artifacts: ArtifactStore,
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
    receipt: PublicOutputReceipt,
    artifacts: ArtifactStore,
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


def _verify_dependency_fingerprint_sources(
    receipt: PublicOutputReceipt,
    artifacts: ArtifactStore,
) -> None:
    if receipt.citations is None:
        return

    for fingerprint in receipt.citations.dependency_fingerprints:
        try:
            envelope = artifacts.get(fingerprint.dependency_id)
        except KeyError as exc:
            raise ProjectionReplayBlocked(
                f"Projection replay missing artifact: {fingerprint.dependency_id}."
            ) from exc
        if envelope.artifact_kind != fingerprint.dependency_kind:
            raise ProjectionReplayBlocked(
                "Projection replay artifact kind mismatch: "
                f"{fingerprint.dependency_id}."
            )
        if envelope.body.get("fingerprint") != fingerprint.fingerprint:
            raise ProjectionReplayBlocked(
                "Projection replay dependency fingerprint mismatch: "
                f"{fingerprint.dependency_id}."
            )
        if envelope.body.get("digest_alg") != fingerprint.digest_alg:
            raise ProjectionReplayBlocked(
                "Projection replay dependency fingerprint algorithm mismatch: "
                f"{fingerprint.dependency_id}."
            )
        if envelope.body.get("dependency_kind") != fingerprint.dependency_kind:
            raise ProjectionReplayBlocked(
                "Projection replay dependency fingerprint kind mismatch: "
                f"{fingerprint.dependency_id}."
            )
        if envelope.body.get("dependency_id") != fingerprint.dependency_id:
            raise ProjectionReplayBlocked(
                "Projection replay dependency fingerprint id mismatch: "
                f"{fingerprint.dependency_id}."
            )
        _verify_profile_lock_body(fingerprint, envelope.body)


def _verify_profile_lock_body(
    fingerprint: DependencyFingerprint,
    body: Mapping[str, Any],
) -> None:
    if fingerprint.dependency_kind != "compiler_profile":
        return
    profile_lock = body.get("profile_lock")
    if profile_lock is None:
        return
    if not isinstance(profile_lock, Mapping):
        raise ProjectionReplayBlocked(
            "Projection replay profile lock body is malformed: "
            f"{fingerprint.dependency_id}."
        )
    recomputed = DependencyFingerprint.from_payload(
        dependency_kind=fingerprint.dependency_kind,
        dependency_id=fingerprint.dependency_id,
        payload=profile_lock,
    )
    if recomputed.fingerprint != fingerprint.fingerprint:
        raise ProjectionReplayBlocked(
            "Projection replay profile lock fingerprint mismatch: "
            f"{fingerprint.dependency_id}."
        )


def _verify_source_evidence_span_fingerprints(
    receipt: PublicOutputReceipt,
    artifacts: ArtifactStore,
) -> None:
    if receipt.citations is None:
        return

    for fingerprint in receipt.citations.dependency_fingerprints:
        if fingerprint.dependency_kind != "evidence_witness":
            continue
        envelope = artifacts.get(fingerprint.dependency_id)
        actual = _evidence_witness_fingerprint_from_body(envelope.body)
        if actual.fingerprint != fingerprint.fingerprint:
            raise ProjectionReplayBlocked(
                "Projection replay source evidence fingerprint mismatch: "
                f"{fingerprint.dependency_id}."
            )


def _evidence_witness_fingerprint_from_body(
    body: Mapping[str, Any],
) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="evidence_witness",
        dependency_id=str(body.get("witness_id", "")),
        payload={
            "witness_id": body.get("witness_id"),
            "field": body.get("field"),
            "source": body.get("source"),
            "span": body.get("span"),
            "text": body.get("text"),
        },
    )


def _verify_reference_catalog_snapshot_coverage(
    receipt: PublicOutputReceipt,
    artifacts: ArtifactStore,
) -> None:
    if receipt.citations is None:
        return

    reference_records = tuple(
        fingerprint
        for fingerprint in receipt.citations.dependency_fingerprints
        if fingerprint.dependency_kind == "reference_record"
    )
    catalog_snapshots = tuple(
        fingerprint
        for fingerprint in receipt.citations.dependency_fingerprints
        if fingerprint.dependency_kind == "reference_catalog_snapshot"
    )
    if not reference_records or not catalog_snapshots:
        return

    covered_records: set[tuple[str, str]] = set()
    for snapshot in catalog_snapshots:
        envelope = artifacts.get(snapshot.dependency_id)
        covered_records.update(_catalog_snapshot_record_keys(envelope.body))

    for fingerprint in reference_records:
        record_key = (fingerprint.dependency_id, fingerprint.fingerprint)
        if record_key not in covered_records:
            raise ProjectionReplayBlocked(
                "Projection replay catalog snapshot missing reference record: "
                f"{fingerprint.dependency_id}."
            )


def _catalog_snapshot_record_keys(
    snapshot_body: Mapping[str, Any],
) -> set[tuple[str, str]]:
    records = snapshot_body.get("record_fingerprints", ())
    record_keys: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, Mapping):
            continue
        dependency_id = record.get("dependency_id")
        fingerprint = record.get("fingerprint")
        if isinstance(dependency_id, str) and isinstance(fingerprint, str):
            record_keys.add((dependency_id, fingerprint))
    return record_keys


def _unique_refs(refs: list[ArtifactRef]) -> tuple[ArtifactRef, ...]:
    seen: set[ArtifactRef] = set()
    unique: list[ArtifactRef] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return tuple(unique)


def _dependency_fingerprints(
    receipt: PublicOutputReceipt,
) -> tuple[DependencyFingerprint, ...]:
    if receipt.citations is None:
        return ()
    return receipt.citations.dependency_fingerprints


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = [
    "ArtifactRef",
    "ProjectionReplayReport",
    "receipt_artifact_refs",
    "replay_public_projection",
]
