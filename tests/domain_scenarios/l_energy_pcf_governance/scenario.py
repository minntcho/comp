from __future__ import annotations

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import prepare_commit
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    build_domain_scenario_result,
)
from tests.domain_scenarios.l_energy_pcf_governance.expected import (
    EXPECTED_DERIVED_CLAIM_IDS,
    EXPECTED_FORMULA_IDS,
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_BINDING_IDS,
    EXPECTED_SOURCE_REFS,
    EXPECTED_TRACE_IDS,
    SCENARIO_ID,
)
from tests.domain_scenarios.l_energy_pcf_governance.fixtures import (
    PROFILE_ID,
    PUBLIC_ROW_ID,
    SUBJECT_ID,
    compile_report,
)


RESOLVER_STEPS = (
    "load_platform_expected_receipt_fixture",
    "create_fixture_reference_bindings",
    "create_fixture_derived_claims",
    "prepare_commit",
    "receipt_gated_projection",
)

PROJECTION_FIELDS = (
    "case_id",
    "total_emission_tco2e",
    "packs",
    "total_energy_gwh",
    "kgco2e_per_pack",
    "kgco2e_per_kwh",
)
PROJECTION_ID = "l-energy-pcf-public-row"

SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="L-Energy PCF Governance",
    run=lambda: run_l_energy_pcf_governance_scenario(),
    source_refs=EXPECTED_SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_reference_binding_ids=EXPECTED_REFERENCE_BINDING_IDS,
        required_derived_claim_ids=EXPECTED_DERIVED_CLAIM_IDS,
        required_receipt_reference_binding_ids=EXPECTED_REFERENCE_BINDING_IDS,
        required_receipt_derived_claim_ids=EXPECTED_DERIVED_CLAIM_IDS,
        required_receipt_calculation_trace_ids=EXPECTED_TRACE_IDS,
        required_receipt_formula_ids=EXPECTED_FORMULA_IDS,
    ),
)


def run_l_energy_pcf_governance_scenario() -> DomainScenarioResult:
    report = compile_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
    )
    projection = None
    if preparation.receipt is not None:
        projection = project_public_row(
            _projection_source(report),
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=preparation.receipt,
        )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def _projection_source(report) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


__all__ = ["SCENARIO", "run_l_energy_pcf_governance_scenario"]
