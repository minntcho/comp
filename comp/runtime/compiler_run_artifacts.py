from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from comp.compiler_tool import (
    CommitPreparation,
    ValidationReport,
    evidence_ref_fingerprint,
)
from comp.persistence import ArtifactMaterial, ArtifactRef, receipt_artifact_refs


class CompilerRunArtifactMaterializationError(RuntimeError):
    """Raised when a compiler run cannot be serialized into artifact material."""


@dataclass(frozen=True)
class ExternalArtifactMaterial:
    artifact_kind: str
    artifact_id: str
    body: Mapping[str, Any]

    @property
    def key(self) -> tuple[str, str]:
        return (self.artifact_kind, self.artifact_id)


@dataclass(frozen=True)
class ExternalArtifactMaterialSource:
    materials: tuple[ExternalArtifactMaterial, ...] = field(default_factory=tuple)

    def __init__(
        self,
        materials: Iterable[ExternalArtifactMaterial] = (),
    ) -> None:
        material_tuple = tuple(materials)
        object.__setattr__(self, "materials", material_tuple)
        object.__setattr__(self, "_bodies", _external_bodies_by_key(material_tuple))

    def body_for(self, ref: ArtifactRef) -> Mapping[str, Any]:
        try:
            return dict(self._bodies[(ref.artifact_kind, ref.artifact_id)])
        except KeyError as exc:
            raise CompilerRunArtifactMaterializationError(
                "Compiler run artifact materialization missing external artifact body: "
                f"{ref.artifact_kind}:{ref.artifact_id}."
            ) from exc


def materialize_compiler_run_artifacts(
    report: ValidationReport,
    preparation: CommitPreparation,
    *,
    external_material_source: ExternalArtifactMaterialSource | None = None,
    schema_version: str = "compiler-run-v1",
) -> tuple[ArtifactMaterial, ...]:
    receipt = preparation.receipt
    if receipt is None:
        raise CompilerRunArtifactMaterializationError(
            "Compiler run artifact materialization requires a receipt."
        )

    material_source = (
        external_material_source
        if external_material_source is not None
        else ExternalArtifactMaterialSource()
    )
    return tuple(
        ArtifactMaterial(
            artifact_id=ref.artifact_id,
            artifact_kind=ref.artifact_kind,
            schema_version=schema_version,
            body=_artifact_body_for_ref(report, preparation, material_source, ref),
        )
        for ref in receipt_artifact_refs(receipt)
    )


def _artifact_body_for_ref(
    report: ValidationReport,
    preparation: CommitPreparation,
    external_material_source: ExternalArtifactMaterialSource,
    ref: ArtifactRef,
) -> Mapping[str, Any]:
    if ref.artifact_kind == "commit_package":
        package = preparation.package
        return {
            "package_id": package.package_id,
            "subject_id": package.subject_id,
            "report_status": package.report_status,
            "complete": package.complete,
            "checked_claim_fields": package.checked_claim_fields,
            "checked_claim_witness_ids": package.checked_claim_witness_ids,
            "semantic_judgment_ids": package.semantic_judgment_ids,
            "reference_binding_ids": package.reference_binding_ids,
            "derived_claim_fields": package.derived_claim_fields,
            "derived_claim_ids": package.derived_claim_ids,
            "calculation_trace_ids": package.calculation_trace_ids,
            "formula_ids": package.formula_ids,
            "open_obligation_ids": package.open_obligation_ids,
            "resolved_obligation_ids": package.resolved_obligation_ids,
            "hazard_ids": package.hazard_ids,
            "profile_id": package.profile_id,
            "projection_value_commitments": tuple(
                _projection_value_commitment_body(commitment)
                for commitment in package.projection_value_commitments
            ),
            "dependency_fingerprints": tuple(
                _dependency_fingerprint_body(fingerprint)
                for fingerprint in package.dependency_fingerprints
            ),
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
        if witness is None:
            return external_material_source.body_for(ref)
        fingerprint = evidence_ref_fingerprint(witness)
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
        binding = _by_id(report.canonical_references, ref.artifact_id, "binding_id")
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
        claim = _by_id(report.calculated_claims, ref.artifact_id, "claim_id")
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
                    "exact_output_value": step.exact_output_value,
                    "rounding_quantum": step.rounding_quantum,
                    "rounding_mode": step.rounding_mode,
                }
                for step in trace.steps
            ),
        }
    if ref.artifact_kind == "formula":
        return {
            "formula_id": ref.artifact_id,
            "derived_claim_ids": tuple(
                claim.claim_id
                for claim in report.calculated_claims
                if claim.formula_id == ref.artifact_id
            ),
        }
    return external_material_source.body_for(ref)


def _external_bodies_by_key(
    materials: tuple[ExternalArtifactMaterial, ...],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    bodies: dict[tuple[str, str], Mapping[str, Any]] = {}
    for material in materials:
        existing = bodies.get(material.key)
        if existing is None:
            bodies[material.key] = dict(material.body)
            continue
        if existing != dict(material.body):
            raise CompilerRunArtifactMaterializationError(
                "Compiler run artifact materialization has conflicting external "
                f"material: {material.artifact_kind}:{material.artifact_id}."
            )
    return bodies


def _projection_value_commitment_body(commitment) -> dict[str, str]:
    return {
        "field": commitment.field,
        "source_kind": commitment.source_kind,
        "source_id": commitment.source_id,
        "value_digest": commitment.value_digest,
        "digest_alg": commitment.digest_alg,
    }


def _dependency_fingerprint_body(fingerprint) -> dict[str, str]:
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _checked_claim_by_source_id(report: ValidationReport, source_id: str):
    for claim in report.checked_claims:
        if source_id == f"checked_claim:{claim.field}:{claim.witness_id}":
            return claim
    raise CompilerRunArtifactMaterializationError(
        f"Compiler run artifact materialization missing checked claim: {source_id}."
    )


def _evidence_witness_by_id(report: ValidationReport, witness_id: str):
    for witness in report.evidence_refs:
        if witness.witness_id == witness_id:
            return witness
    return None


def _trace_by_id(report: ValidationReport, trace_id: str):
    for claim in report.calculated_claims:
        if claim.trace.trace_id == trace_id:
            return claim.trace
    raise CompilerRunArtifactMaterializationError(
        f"Compiler run artifact materialization missing calculation trace: {trace_id}."
    )


def _by_id(items, item_id: str, field: str):
    for item in items:
        if getattr(item, field) == item_id:
            return item
    raise CompilerRunArtifactMaterializationError(
        f"Compiler run artifact materialization missing artifact: {item_id}."
    )


__all__ = [
    "CompilerRunArtifactMaterializationError",
    "ExternalArtifactMaterial",
    "ExternalArtifactMaterialSource",
    "materialize_compiler_run_artifacts",
]
