from __future__ import annotations

from comp import PublicOutputSpec, SubjectRef, build_public_output
from comp.compiler_tool import prepare_commit, resolve_reference_grounded_calculation
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    build_domain_scenario_result,
)
from tests.domain_scenarios.tiny_pcf.expected import (
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
)
from tests.domain_scenarios.tiny_pcf.fixtures import (
    OUTPUT_CLAIM_ID,
    PUBLIC_ROW_ID,
    SCENARIO_ID,
    SUBJECT_ID,
    blocked_report,
    catalog,
    criteria,
    formula,
    input_claim,
    profile,
)


RESOLVER_STEPS = (
    "plan_calculation_resolution",
    "reference_search:keyword",
    "deterministic_reference_selection",
    "retry_calculation",
    "prepare_commit",
    "receipt_gated_projection",
)

SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Tiny PCF location-based electricity",
    run=lambda: run_tiny_pcf_scenario(),
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_requirement_kinds=EXPECTED_RESOLVED_OBLIGATION_KINDS,
        required_reference_candidate_ids=EXPECTED_REFERENCE_CANDIDATE_IDS,
        required_reference_binding_ids=("bind-electricity-factor",),
        required_derived_claim_ids=("tiny-pcf:co2e_kg",),
        required_receipt_reference_binding_ids=("bind-electricity-factor",),
        required_receipt_derived_claim_ids=("tiny-pcf:co2e_kg",),
        required_receipt_calculation_trace_ids=("trace:tiny-pcf:co2e_kg",),
        required_receipt_formula_ids=("pcf.electricity_factor_multiplication.v1",),
    ),
)


def run_tiny_pcf_scenario() -> DomainScenarioResult:
    scenario_profile = profile()
    resolved_report = resolve_reference_grounded_calculation(
        blocked_report(),
        catalog(),
        query_for_requirement=lambda obligation: (
            "Korea grid electricity factor 2024"
            if obligation.kind == "reference_search_required"
            else None
        ),
        criteria=criteria(),
        input_claim=input_claim(),
        formula=formula(),
        output_claim_id=OUTPUT_CLAIM_ID,
    )
    preparation = prepare_commit(
        resolved_report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id="pcf-public-row",
        profile_id=scenario_profile.profile_id,
    )
    projection = None
    if preparation.receipt is not None:
        projection = build_public_output(
            _projection_source(resolved_report),
            PublicOutputSpec("pcf-public-row", ("electricity_kwh", "co2e_kg")),
            receipt=preparation.receipt,
        )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=resolved_report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def _projection_source(report) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values


__all__ = ["SCENARIO", "run_tiny_pcf_scenario"]
