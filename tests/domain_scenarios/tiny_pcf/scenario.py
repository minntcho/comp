from __future__ import annotations

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import prepare_commit, resolve_reference_grounded_calculation
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    build_domain_scenario_result,
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


def run_tiny_pcf_scenario() -> DomainScenarioResult:
    scenario_profile = profile()
    resolved_report = resolve_reference_grounded_calculation(
        blocked_report(),
        catalog(),
        query_for_obligation=lambda obligation: (
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
        profile_id=scenario_profile.profile_id,
    )
    projection = None
    if preparation.receipt is not None:
        projection = project_public_row(
            _projection_source(resolved_report),
            ProjectionSpec("pcf-public-row", ("electricity_kwh", "co2e_kg")),
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
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


__all__ = ["run_tiny_pcf_scenario"]
