from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp.compiler_tool import (
    CommitPreparation,
    CompileReport,
    evidence_witness_fingerprint,
)
from comp.judgment import ProjectionSpec
from comp.persistence import (
    ArtifactEnvelope,
    ArtifactRef,
    InMemoryArtifactStore,
    InMemoryReceiptLedger,
    ProjectionReplayReport,
    receipt_artifact_refs,
    replay_public_projection,
)


@dataclass(frozen=True)
class SyntheticReplayBundle:
    artifacts: InMemoryArtifactStore
    receipt_ledger: InMemoryReceiptLedger


def synthetic_replay_bundle(
    report: CompileReport,
    preparation: CommitPreparation,
    dependency_artifact_bodies: Mapping[tuple[str, str], Mapping[str, Any]],
) -> SyntheticReplayBundle:
    receipt = preparation.receipt
    if receipt is None:
        raise AssertionError("Synthetic replay requires a commit receipt.")

    artifacts = InMemoryArtifactStore()
    for ref in receipt_artifact_refs(receipt):
        artifacts.record(
            _artifact_envelope_for_ref(
                report,
                preparation,
                dependency_artifact_bodies,
                ref,
            )
        )

    receipt_ledger = InMemoryReceiptLedger()
    receipt_ledger.record(receipt)
    return SyntheticReplayBundle(
        artifacts=artifacts,
        receipt_ledger=receipt_ledger,
    )


def replay_synthetic_projection(
    row: Mapping[str, Any],
    projection: ProjectionSpec,
    preparation: CommitPreparation,
    *,
    bundle: SyntheticReplayBundle,
) -> ProjectionReplayReport:
    receipt = preparation.receipt
    if receipt is None:
        raise AssertionError("Synthetic replay requires a commit receipt.")

    ledger_receipt = bundle.receipt_ledger.get(
        public_row_id=receipt.public_row_id,
        projection_id=receipt.projection_id,
        draft_id=receipt.draft_id,
    )
    return replay_public_projection(
        row,
        projection,
        receipt=ledger_receipt,
        artifacts=bundle.artifacts,
    )


def _artifact_envelope_for_ref(
    report: CompileReport,
    preparation: CommitPreparation,
    dependency_artifact_bodies: Mapping[tuple[str, str], Mapping[str, Any]],
    ref: ArtifactRef,
) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id=ref.artifact_id,
        artifact_kind=ref.artifact_kind,
        schema_version="synthetic-scenario-v1",
        body=_artifact_body_for_ref(
            report,
            preparation,
            dependency_artifact_bodies,
            ref,
        ),
    )


def _artifact_body_for_ref(
    report: CompileReport,
    preparation: CommitPreparation,
    dependency_artifact_bodies: Mapping[tuple[str, str], Mapping[str, Any]],
    ref: ArtifactRef,
) -> dict[str, Any]:
    dependency_body = dependency_artifact_bodies.get(
        (ref.artifact_kind, ref.artifact_id)
    )
    if dependency_body is not None:
        return dict(dependency_body)

    if ref.artifact_kind == "commit_package":
        package = preparation.package
        return {
            "package_id": package.package_id,
            "subject_id": package.subject_id,
            "report_status": package.report_status,
            "complete": package.complete,
            "reference_binding_ids": package.reference_binding_ids,
            "derived_claim_ids": package.derived_claim_ids,
            "calculation_trace_ids": package.calculation_trace_ids,
            "formula_ids": package.formula_ids,
            "open_obligation_ids": package.open_obligation_ids,
            "hazard_ids": package.hazard_ids,
        }
    if ref.artifact_kind == "governance_decision":
        decision = preparation.decision
        return {
            "decision_id": decision.decision_id,
            "package_id": decision.package_id,
            "subject_id": decision.subject_id,
            "status": decision.status,
            "reasons": decision.reasons,
            "profile_id": decision.profile_id,
        }
    if ref.artifact_kind == "checked_claim":
        claim = _checked_claim_by_source_id(report, ref.artifact_id)
        return {
            "claim_id": ref.artifact_id,
            "field": claim.field,
            "value": claim.value,
            "witness_id": claim.witness_id,
            "origin": claim.origin,
        }
    if ref.artifact_kind == "evidence_witness":
        witness = _evidence_witness_by_id(report, ref.artifact_id)
        fingerprint = evidence_witness_fingerprint(witness)
        return {
            "dependency_kind": fingerprint.dependency_kind,
            "dependency_id": fingerprint.dependency_id,
            "witness_id": witness.witness_id,
            "field": witness.field,
            "source": witness.source,
            "span": witness.span,
            "text": witness.text,
            "fingerprint": fingerprint.fingerprint,
            "digest_alg": fingerprint.digest_alg,
        }
    if ref.artifact_kind == "reference_binding":
        binding = _by_id(report.reference_bindings, ref.artifact_id, "binding_id")
        return {
            "binding_id": binding.binding_id,
            "claim_id": binding.claim_id,
            "reference_id": binding.reference_id,
            "reference_type": binding.reference_type,
            "selected_candidate_id": binding.selected_candidate_id,
            "selector_rule_id": binding.selector_rule_id,
            "source_witness_ids": binding.source_witness_ids,
            "rejected_candidates": tuple(
                {
                    "candidate_id": candidate.candidate_id,
                    "reference_id": candidate.reference_id,
                    "reason": candidate.reason,
                    "selector_rule_id": candidate.selector_rule_id,
                }
                for candidate in binding.rejected_candidates
            ),
            "authority": binding.authority,
        }
    if ref.artifact_kind == "derived_claim":
        claim = _by_id(report.derived_claims, ref.artifact_id, "claim_id")
        return {
            "claim_id": claim.claim_id,
            "field": claim.field,
            "value": claim.value,
            "unit": claim.unit,
            "formula_id": claim.formula_id,
            "trace_id": claim.trace.trace_id,
            "origin": claim.origin,
        }
    if ref.artifact_kind == "calculation_trace":
        trace = _trace_by_id(report, ref.artifact_id)
        return {
            "trace_id": trace.trace_id,
            "formula_id": trace.formula_id,
            "input_claim_ids": trace.input_claim_ids,
            "reference_binding_ids": trace.reference_binding_ids,
            "steps": tuple(
                {
                    "step_id": step.step_id,
                    "operation": step.operation,
                    "input_ids": step.input_ids,
                    "output_value": step.output_value,
                    "output_unit": step.output_unit,
                }
                for step in trace.steps
            ),
        }
    if ref.artifact_kind == "formula":
        return {"formula_id": ref.artifact_id}

    raise AssertionError(f"Unsupported synthetic artifact ref: {ref}.")


def _checked_claim_by_source_id(report: CompileReport, source_id: str):
    for claim in report.checked_claims:
        if source_id == f"checked_claim:{claim.field}:{claim.witness_id}":
            return claim
    raise AssertionError(f"Synthetic checked claim not found: {source_id}.")


def _evidence_witness_by_id(report: CompileReport, witness_id: str):
    for witness in report.evidence_witnesses:
        if witness.witness_id == witness_id:
            return witness
    raise AssertionError(f"Synthetic evidence witness not found: {witness_id}.")


def _trace_by_id(report: CompileReport, trace_id: str):
    for claim in report.derived_claims:
        if claim.trace.trace_id == trace_id:
            return claim.trace
    raise AssertionError(f"Synthetic calculation trace not found: {trace_id}.")


def _by_id(items, item_id: str, field: str):
    for item in items:
        if getattr(item, field) == item_id:
            return item
    raise AssertionError(f"Synthetic artifact not found: {item_id}.")


__all__ = [
    "SyntheticReplayBundle",
    "replay_synthetic_projection",
    "synthetic_replay_bundle",
]
