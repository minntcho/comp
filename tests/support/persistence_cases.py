from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    DependencyFingerprint,
    ProjectionSpec,
    ProjectionValueCommitment,
)
from comp.persistence import ArtifactEnvelope, ArtifactRef, InMemoryArtifactStore
from comp.persistence import receipt_artifact_refs


@dataclass(frozen=True, slots=True)
class PersistenceProjectionCase:
    receipt: CommitReceipt
    projection: ProjectionSpec
    source_values: dict[str, Any]
    public_row: dict[str, Any]


def receipt_projection_case(
    *,
    amount: int = 100,
    site: str = "plant-a",
) -> PersistenceProjectionCase:
    commitments = (
        ProjectionValueCommitment.from_value(
            field="site",
            source_kind="checked_claim",
            source_id="checked_claim:site:span-site",
            value=site,
        ),
        ProjectionValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:span-amount",
            value=amount,
        ),
    )
    citations = CommitReceiptCitations(
        governance_decision_id="decision-1",
        governance_status="commit",
        governance_reasons=("ready",),
        commit_package_id="package-1",
        commit_package_complete=True,
        subject_id="facility-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        profile_id=None,
        report_status="accepted",
        checked_claim_fields=("site", "amount"),
        checked_claim_witness_ids=("span-site", "span-amount"),
        semantic_judgment_ids=(),
        reference_binding_ids=(),
        derived_claim_fields=(),
        derived_claim_ids=(),
        calculation_trace_ids=(),
        formula_ids=(),
        resolved_obligation_ids=(),
        open_obligation_ids=(),
        hazard_ids=(),
        projection_value_commitments=commitments,
        dependency_fingerprints=(
            DependencyFingerprint(
                dependency_kind="compiler_profile",
                dependency_id="fixture-profile",
                fingerprint="sha256:fixture-profile",
            ),
            DependencyFingerprint(
                dependency_kind="reference_record",
                dependency_id="fixture-factor",
                fingerprint="sha256:fixture-factor",
            ),
            DependencyFingerprint(
                dependency_kind="reference_catalog_snapshot",
                dependency_id="reference_catalog_snapshot:fixture-catalog:2026.1",
                fingerprint="sha256:fixture-reference-catalog-snapshot",
            ),
        ),
    )
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("decision-1",),
        barrier_snapshot=citations.to_barrier_snapshot(),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=citations,
    )
    projection = ProjectionSpec("public-row", ("site", "amount"))
    public_row = {"site": site, "amount": amount}
    return PersistenceProjectionCase(
        receipt=receipt,
        projection=projection,
        source_values=dict(public_row),
        public_row=public_row,
    )


def claim_envelope(
    *,
    value: int = 1200,
    artifact_id: str = "artifact:claim:1",
) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id=artifact_id,
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": value},
    )


def artifact_store_for_receipt(
    receipt: CommitReceipt,
    *,
    committed_values: Mapping[str, Any] | None = None,
    skip: ArtifactRef | None = None,
    override: ArtifactEnvelope | None = None,
) -> InMemoryArtifactStore:
    store = InMemoryArtifactStore()
    for ref in receipt_artifact_refs(receipt):
        if ref == skip:
            continue
        if override is not None and override.artifact_id == ref.artifact_id:
            store.record(override)
            continue
        store.record(artifact_for_ref(ref, committed_values=committed_values))
    return store


def artifact_for_ref(
    ref: ArtifactRef,
    *,
    committed_values: Mapping[str, Any] | None = None,
) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id=ref.artifact_id,
        artifact_kind=ref.artifact_kind,
        schema_version="v1",
        body=artifact_body_for_ref(ref, committed_values=committed_values),
    )


def artifact_body_for_ref(
    ref: ArtifactRef,
    *,
    committed_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if ref.artifact_kind == "commit_package":
        return {"package_id": ref.artifact_id, "complete": True}
    if ref.artifact_kind == "governance_decision":
        return {"decision_id": ref.artifact_id, "status": "commit"}
    if ref.artifact_kind == "checked_claim":
        field = _claim_field(ref)
        body = {"claim_id": ref.artifact_id, "field": field}
        values = committed_values or {}
        if field in values:
            body["value"] = values[field]
        return body
    if ref.artifact_kind == "evidence_witness":
        return {"witness_id": ref.artifact_id, "source": "fixture"}
    if ref.artifact_kind in {
        "compiler_profile",
        "reference_record",
        "reference_catalog_snapshot",
    }:
        return _dependency_fingerprint_body(ref)
    raise AssertionError(f"Unexpected artifact ref in test: {ref}")


def _claim_field(ref: ArtifactRef) -> str:
    if ":site:" in ref.artifact_id:
        return "site"
    if ":amount:" in ref.artifact_id:
        return "amount"
    return "unknown"


def _dependency_fingerprint_body(ref: ArtifactRef) -> dict[str, Any]:
    if ref.artifact_id == "fixture-profile":
        return {
            "dependency_kind": "compiler_profile",
            "dependency_id": "fixture-profile",
            "fingerprint": "sha256:fixture-profile",
            "digest_alg": "sha256",
        }
    if ref.artifact_id == "fixture-factor":
        return {
            "dependency_kind": "reference_record",
            "dependency_id": "fixture-factor",
            "fingerprint": "sha256:fixture-factor",
            "digest_alg": "sha256",
        }
    if ref.artifact_id == "reference_catalog_snapshot:fixture-catalog:2026.1":
        return {
            "dependency_kind": "reference_catalog_snapshot",
            "dependency_id": "reference_catalog_snapshot:fixture-catalog:2026.1",
            "fingerprint": "sha256:fixture-reference-catalog-snapshot",
            "digest_alg": "sha256",
            "record_fingerprints": (
                {
                    "dependency_kind": "reference_record",
                    "dependency_id": "fixture-factor",
                    "fingerprint": "sha256:fixture-factor",
                    "digest_alg": "sha256",
                },
            ),
        }
    raise AssertionError(f"Unexpected dependency fingerprint ref in test: {ref}")


__all__ = [
    "PersistenceProjectionCase",
    "artifact_body_for_ref",
    "artifact_for_ref",
    "artifact_store_for_receipt",
    "claim_envelope",
    "receipt_projection_case",
]
