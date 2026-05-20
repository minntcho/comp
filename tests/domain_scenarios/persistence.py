from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
from tests.domain_scenarios.core import DomainScenarioResult


@dataclass(frozen=True)
class DomainScenarioReplayBundle:
    artifacts: InMemoryArtifactStore
    receipt_ledger: InMemoryReceiptLedger


def scenario_replay_bundle(
    result: DomainScenarioResult,
    *,
    skip: ArtifactRef | None = None,
    override: ArtifactEnvelope | None = None,
) -> DomainScenarioReplayBundle:
    receipt = result.preparation.receipt
    if receipt is None:
        raise AssertionError("Scenario replay requires a commit receipt.")

    artifacts = InMemoryArtifactStore()
    for ref in receipt_artifact_refs(receipt):
        if ref == skip:
            continue
        if override is not None and override.artifact_id == ref.artifact_id:
            artifacts.record(override)
            continue
        artifacts.record(_artifact_envelope_for_ref(result, ref))

    receipt_ledger = InMemoryReceiptLedger()
    receipt_ledger.record(receipt)
    return DomainScenarioReplayBundle(
        artifacts=artifacts,
        receipt_ledger=receipt_ledger,
    )


def replay_scenario_projection(
    result: DomainScenarioResult,
    projection: ProjectionSpec,
    *,
    bundle: DomainScenarioReplayBundle | None = None,
) -> ProjectionReplayReport:
    receipt = result.preparation.receipt
    if receipt is None:
        raise AssertionError("Scenario replay requires a commit receipt.")
    if result.projection is None:
        raise AssertionError("Scenario replay requires a materialized projection.")

    replay_bundle = bundle or scenario_replay_bundle(result)
    ledger_receipt = replay_bundle.receipt_ledger.get(
        public_row_id=receipt.public_row_id,
        projection_id=receipt.projection_id,
        draft_id=receipt.draft_id,
    )
    return replay_public_projection(
        result.projection,
        projection,
        receipt=ledger_receipt,
        artifacts=replay_bundle.artifacts,
    )


def _artifact_envelope_for_ref(
    result: DomainScenarioResult,
    ref: ArtifactRef,
) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id=ref.artifact_id,
        artifact_kind=ref.artifact_kind,
        schema_version="domain-scenario-v1",
        body=_artifact_body_for_ref(result, ref),
    )


def _artifact_body_for_ref(
    result: DomainScenarioResult,
    ref: ArtifactRef,
) -> dict[str, Any]:
    if ref.artifact_kind == "commit_package":
        package = result.preparation.package
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
        decision = result.preparation.decision
        return {
            "decision_id": decision.decision_id,
            "package_id": decision.package_id,
            "subject_id": decision.subject_id,
            "status": decision.status,
            "reasons": decision.reasons,
            "profile_id": decision.profile_id,
        }
    if ref.artifact_kind == "checked_claim":
        claim = _checked_claim_by_source_id(result, ref.artifact_id)
        return {
            "claim_id": ref.artifact_id,
            "field": claim.field,
            "value": claim.value,
            "witness_id": claim.witness_id,
            "origin": claim.origin,
        }
    if ref.artifact_kind == "evidence_witness":
        return {"witness_id": ref.artifact_id, "source": "domain_scenario"}
    if ref.artifact_kind == "reference_binding":
        binding = _by_id(
            result.report.reference_bindings,
            ref.artifact_id,
            "binding_id",
        )
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
        claim = _by_id(result.report.derived_claims, ref.artifact_id, "claim_id")
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
        trace = _trace_by_id(result, ref.artifact_id)
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
    if ref.artifact_kind == "semantic_judgment":
        return {"judgment_id": ref.artifact_id}
    if ref.artifact_kind in {"compiler_profile", "reference_record"}:
        return _dependency_fingerprint_body(result, ref)
    raise AssertionError(f"Unsupported scenario artifact ref: {ref}.")


def _checked_claim_by_source_id(result: DomainScenarioResult, source_id: str):
    for claim in result.report.checked_claims:
        if source_id == f"checked_claim:{claim.field}:{claim.witness_id}":
            return claim
    raise AssertionError(f"Scenario checked claim not found: {source_id}.")


def _trace_by_id(result: DomainScenarioResult, trace_id: str):
    for claim in result.report.derived_claims:
        if claim.trace.trace_id == trace_id:
            return claim.trace
    raise AssertionError(f"Scenario calculation trace not found: {trace_id}.")


def _by_id(items, item_id: str, field: str):
    for item in items:
        if getattr(item, field) == item_id:
            return item
    raise AssertionError(f"Scenario artifact not found: {item_id}.")


def _dependency_fingerprint_body(
    result: DomainScenarioResult,
    ref: ArtifactRef,
) -> dict[str, str]:
    receipt = result.preparation.receipt
    if receipt is None or receipt.citations is None:
        raise AssertionError("Scenario dependency fingerprint requires a receipt.")
    for fingerprint in receipt.citations.dependency_fingerprints:
        if (
            fingerprint.dependency_kind == ref.artifact_kind
            and fingerprint.dependency_id == ref.artifact_id
        ):
            return {
                "dependency_kind": fingerprint.dependency_kind,
                "dependency_id": fingerprint.dependency_id,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
            }
    raise AssertionError(f"Scenario dependency fingerprint not found: {ref}.")


__all__ = [
    "DomainScenarioReplayBundle",
    "replay_scenario_projection",
    "scenario_replay_bundle",
]
