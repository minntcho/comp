from __future__ import annotations

from comp import PublicOutputSpec, SubjectRef, build_public_output
from comp.compiler_tool import prepare_commit, resolve_reference_grounded_calculation
from comp.scenarios.synthetic import (
    SyntheticPcfAdapter,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
)
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)
from tests.domain_scenarios.synthetic_pcf_smoke.expected import (
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
)


SCENARIO_ID = "synthetic_pcf.smoke.v1"
RESOLVER_STEPS = (
    "synthetic_scenario_generator",
    "raw_sources_only_adapter",
    "compiler_tool.compile_interpretation",
    "plan_calculation_resolution",
    "reference_search:oracle_excluded",
    "deterministic_reference_selection",
    "retry_calculation",
    "prepare_commit",
    "receipt_gated_projection",
)


SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic PCF smoke scenario",
    run=lambda: run_synthetic_pcf_smoke_scenario(),
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_requirement_kinds=EXPECTED_RESOLVED_OBLIGATION_KINDS,
        required_reference_candidate_ids=EXPECTED_REFERENCE_CANDIDATE_IDS,
        required_reference_binding_ids=("bind-synthetic-electricity-factor",),
        required_derived_claim_ids=("synthetic-pcf-smoke:electricity:co2e_kg",),
        required_receipt_reference_binding_ids=("bind-synthetic-electricity-factor",),
        required_receipt_derived_claim_ids=(
            "synthetic-pcf-smoke:electricity:co2e_kg",
        ),
        required_receipt_calculation_trace_ids=(
            "trace:synthetic-pcf-smoke:electricity:co2e_kg",
        ),
        required_receipt_formula_ids=("pcf.electricity_factor_multiplication.v1",),
    ),
)


def run_synthetic_pcf_smoke_scenario() -> DomainScenarioResult:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    adapter = SyntheticPcfAdapter(run.input_bundle)
    report = resolve_reference_grounded_calculation(
        adapter.blocked_report(),
        adapter.reference_catalog(),
        query_for_requirement=adapter.query_for_requirement,
        criteria=adapter.reference_selection_criteria(),
        input_claim=adapter.input_claim(),
        formula=adapter.formula(),
        output_claim_id=adapter.output_claim_id,
    )
    preparation = prepare_commit(
        report,
        subject_id=adapter.subject_id,
        public_row_id=adapter.public_row_id,
        projection_id=adapter.projection_id,
        profile_id=adapter.profile_id,
        dependency_fingerprints=adapter.dependency_fingerprints(),
    )
    projection = None
    if preparation.receipt is not None:
        projection = build_public_output(
            adapter.projection_source(report),
            PublicOutputSpec(adapter.projection_id, adapter.projection_fields),
            receipt=preparation.receipt,
        )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", adapter.subject_id),
        resolver_steps=RESOLVER_STEPS,
        external_material_source=adapter.external_material_source(),
    )


__all__ = ["SCENARIO", "run_synthetic_pcf_smoke_scenario"]
