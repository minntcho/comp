from __future__ import annotations

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    ExpectedArtifactRef,
    ExpectedDependencyRef,
    ExpectedObligation,
    ExpectedReceipt,
    ExpectedResolutionArtifact,
    SyntheticResolutionArtifact,
)
from comp.scenarios.synthetic.sources import synthetic_source_dependency_refs


def expected_smoke_receipt(
    config: SyntheticScenarioConfig,
    *,
    source_witness_id: str,
    derived_value: int | float,
    resolved_obligation_ids: tuple[str, ...] | None = None,
) -> ExpectedReceipt:
    commit_package_id = f"commit-package:{config.subject_id}"
    governance_decision_id = f"governance-decision:{commit_package_id}"
    manifest_dependency_id = synthetic_manifest_dependency_id(config)
    resolved_ids = resolved_obligation_ids or (
        reference_search_obligation_id(config),
        calculation_obligation_id(config),
    )
    source_dependency_refs = synthetic_source_dependency_refs(config)
    return ExpectedReceipt(
        public_row_id=config.public_row_id,
        projection_id=config.projection_id,
        authorized_fields=("electricity_kwh", "co2e_kg"),
        public_row={
            "electricity_kwh": config.electricity_kwh,
            "co2e_kg": derived_value,
        },
        governance_status="commit",
        commit_package_id=commit_package_id,
        governance_decision_id=governance_decision_id,
        checked_claim_witness_ids=(source_witness_id,),
        reference_binding_ids=(config.binding_id,),
        derived_claim_ids=(config.output_claim_id,),
        calculation_trace_ids=(f"trace:{config.output_claim_id}",),
        formula_ids=(config.formula_id,),
        resolved_obligation_ids=resolved_ids,
        dependency_refs=(
            ExpectedDependencyRef(
                dependency_kind="synthetic_manifest",
                dependency_id=manifest_dependency_id,
            ),
            *source_dependency_refs,
        ),
        artifact_refs=(
            ExpectedArtifactRef(commit_package_id, "commit_package"),
            ExpectedArtifactRef(governance_decision_id, "governance_decision"),
            ExpectedArtifactRef(
                f"checked_claim:electricity_kwh:{source_witness_id}",
                "checked_claim",
            ),
            ExpectedArtifactRef(config.output_claim_id, "derived_claim"),
            ExpectedArtifactRef(source_witness_id, "evidence_witness"),
            ExpectedArtifactRef(config.binding_id, "reference_binding"),
            ExpectedArtifactRef(
                f"trace:{config.output_claim_id}",
                "calculation_trace",
            ),
            ExpectedArtifactRef(config.formula_id, "formula"),
            ExpectedArtifactRef(manifest_dependency_id, "synthetic_manifest"),
            *(
                ExpectedArtifactRef(
                    ref.dependency_id,
                    ref.dependency_kind,
                )
                for ref in source_dependency_refs
            ),
        ),
    )


def synthetic_manifest_dependency_id(config: SyntheticScenarioConfig) -> str:
    return f"synthetic_manifest:{config.scenario_id}:seed-{config.seed}"


def expected_reference_search_obligation(
    config: SyntheticScenarioConfig,
) -> ExpectedObligation:
    return ExpectedObligation(
        obligation_id=reference_search_obligation_id(config),
        kind="reference_search_required",
        field="co2e_kg",
        reason="unknown_reference",
    )


def expected_calculation_obligation(
    config: SyntheticScenarioConfig,
) -> ExpectedObligation:
    return ExpectedObligation(
        obligation_id=calculation_obligation_id(config),
        kind="calculation_blocked",
        field="co2e_kg",
        reason="unknown_reference",
    )


def expected_resolution_artifact(
    resolution: SyntheticResolutionArtifact,
) -> ExpectedResolutionArtifact:
    return ExpectedResolutionArtifact(
        artifact_id=resolution.artifact_id,
        obligation_id=resolution.obligation_id,
        source_row_id=resolution.source_row_id,
        field=resolution.field,
        resolved_value=resolution.resolved_value,
        witness_id=resolution.witness_id,
        source_ref=resolution.source_ref,
    )


def reference_search_obligation_id(config: SyntheticScenarioConfig) -> str:
    return (
        f"resolve:{config.formula_id}:{config.output_claim_id}:"
        "reference_search_required"
    )


def calculation_obligation_id(config: SyntheticScenarioConfig) -> str:
    return (
        f"calculation:{config.formula_id}:{config.output_claim_id}:"
        "unknown_reference"
    )


__all__ = [
    "calculation_obligation_id",
    "expected_calculation_obligation",
    "expected_reference_search_obligation",
    "expected_resolution_artifact",
    "expected_smoke_receipt",
    "reference_search_obligation_id",
    "synthetic_manifest_dependency_id",
]
