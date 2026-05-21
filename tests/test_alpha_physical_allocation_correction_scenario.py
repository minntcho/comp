import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.alpha_physical_allocation_correction import (
    ALPHA_PHYSICAL_ALLOCATION_SCENARIO,
    ELECTRICITY_BINDING_ID,
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    LNG_BINDING_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    run_alpha_physical_allocation_correction_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_alpha_physical_allocation_uses_residence_time_weight():
    result = run_alpha_physical_allocation_correction_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "target-weight-ton-hours": 44000,
        "comparison-weight-ton-hours": 56000,
        "allocation-weight": 0.44,
        "allocated-electricity-mwh": 8800,
        "electricity-emission-tco2e": 4206.4,
        "lng-emission-tco2e": 1100,
        "rounded-final-emission-tco2e": 5306,
    }


def test_alpha_physical_allocation_binds_electricity_and_lng_factors():
    result = run_alpha_physical_allocation_correction_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (ELECTRICITY_BINDING_ID, "platform.factor.electricity_mwh", "emission_factor"),
        (LNG_BINDING_ID, "platform.factor.lng_nm3", "emission_factor"),
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        ELECTRICITY_BINDING_ID,
        LNG_BINDING_ID,
    )


def test_alpha_physical_allocation_commits_without_erasing_invalid_context():
    result = run_alpha_physical_allocation_correction_scenario()

    assert result.report.status == "accepted"
    assert result.report.failed_claims == ()
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert "source:alpha-metal-original-invalid-allocation" in tuple(
        witness.witness_id for witness in result.report.evidence_witnesses
    )
    assert "revenue_share" not in tuple(
        claim.value for claim in result.report.checked_claims
    )
    assert "allocation_share" not in tuple(
        claim.field for claim in result.report.checked_claims
    )


def test_alpha_physical_allocation_creates_receipt_and_projection():
    result = run_alpha_physical_allocation_correction_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(ProjectionBlocked, match="value commitment mismatch"):
        project_public_row(
            {
                **EXPECTED_PROJECTION,
                "alpha_metal_final_emission_tco2e": 9999,
            },
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_alpha_physical_allocation_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.alpha_physical_allocation_correction.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(ALPHA_PHYSICAL_ALLOCATION_SCENARIO),
        ALPHA_PHYSICAL_ALLOCATION_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
