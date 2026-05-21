import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import prepare_commit
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.l_materials_composition_rollup import (
    COMPOSITION_FACTOR_BINDING_ID,
    COMPOSITION_TOTAL_OBLIGATION_ID,
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    L_MATERIALS_COMPOSITION_SCENARIO,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    invalid_l_materials_composition_report,
    run_l_materials_composition_rollup_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_l_materials_composition_rollup_calculates_ncm_emission():
    result = run_l_materials_composition_rollup_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "composition-total": 1.0,
        "ncm-emission-tco2e": 174375,
    }
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    ) == (
        ("composition_total", 1.0, None),
        ("l_materials_final_emission_tco2e", 174375, "tCO2e"),
    )


def test_l_materials_composition_binds_ncm_factor_and_shares():
    result = run_l_materials_composition_rollup_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (
            COMPOSITION_FACTOR_BINDING_ID,
            "platform.factor.ncm811_composition",
            "composition_factor",
        ),
    )
    assert {
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    } >= {
        ("actor_id", "l_materials"),
        ("material_family", "NCM811"),
        ("ni_share", 0.8),
        ("co_share", 0.1),
        ("mn_share", 0.1),
        ("production_ton", 11250),
        ("mapped_ncm_factor_tco2e_per_ton", 15.5),
    }
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        COMPOSITION_FACTOR_BINDING_ID,
    )


def test_l_materials_composition_total_is_resolved_context():
    result = run_l_materials_composition_rollup_scenario()

    assert result.report.status == "accepted"
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert tuple(
        (obligation.kind, obligation.field, obligation.reason)
        for obligation in result.report.resolved_obligations
    ) == (
        (
            "composition_total_validated",
            "ncm_composition",
            "shares_sum_to_one",
        ),
    )
    assert COMPOSITION_TOTAL_OBLIGATION_ID in (
        result.preparation.receipt.citations.resolved_obligation_ids
    )


def test_l_materials_invalid_composition_blocks_mapping_and_projection():
    report = invalid_l_materials_composition_report()
    preparation = prepare_commit(
        report,
        subject_id="case:001-l-energy-pcf-governance:l-materials-invalid-composition",
        public_row_id="public-row:l-materials-invalid-composition",
        projection_id=PROJECTION_ID,
    )

    assert report.status == "blocked"
    assert tuple(
        (claim.field, claim.value, claim.reason)
        for claim in report.failed_claims
    ) == (("composition_total", 0.95, "ERR_COMPOSITION_TOTAL"),)
    assert tuple(
        (hazard.kind, hazard.field, hazard.severity)
        for hazard in report.hazards
    ) == (("composition_mapping_error", "ncm_composition", "block"),)
    assert report.reference_bindings == ()
    assert report.derived_claims == ()
    assert preparation.receipt is None
    with pytest.raises(ProjectionBlocked, match="CommitReceipt"):
        project_public_row(
            {"composition_total": 0.95},
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
        )


def test_l_materials_composition_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.l_materials_composition_rollup.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(L_MATERIALS_COMPOSITION_SCENARIO),
        L_MATERIALS_COMPOSITION_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
