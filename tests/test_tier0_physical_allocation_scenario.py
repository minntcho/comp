import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.tier0_physical_allocation import (
    ELECTRICITY_BINDING_ID,
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    LNG_BINDING_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    TIER0_PHYSICAL_ALLOCATION_SCENARIO,
    run_tier0_physical_allocation_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_tier0_physical_allocation_calculates_line_mass_share_and_own_emission():
    result = run_tier0_physical_allocation_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "total-line-mass-ton": 100000,
        "target-allocation-share": 0.5,
        "allocated-electricity-mwh": 3200,
        "allocated-lng-nm3": 75000,
        "electricity-emission-tco2e": 1529.6,
        "lng-emission-tco2e": 165,
        "rounded-own-emission-tco2e": 1695,
    }
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.calculated_claims
    ) == (
        ("target_allocation_share", 0.5, None),
        ("allocated_electricity_mwh", 3200, "MWh"),
        ("allocated_lng_nm3", 75000, "Nm3"),
        ("electricity_emission_tco2e", 1529.6, "tCO2e"),
        ("lng_emission_tco2e", 165, "tCO2e"),
        ("l_energy_own_emission_tco2e", 1695, "tCO2e"),
    )


def test_tier0_physical_allocation_binds_electricity_and_lng_factors():
    result = run_tier0_physical_allocation_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.canonical_references
    ) == (
        (ELECTRICITY_BINDING_ID, "platform.factor.electricity_mwh", "emission_factor"),
        (LNG_BINDING_ID, "platform.factor.lng_nm3", "emission_factor"),
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        ELECTRICITY_BINDING_ID,
        LNG_BINDING_ID,
    )


def test_tier0_physical_allocation_checks_site_inputs_and_dqr():
    result = run_tier0_physical_allocation_scenario()

    assert result.report.status == "accepted"
    assert result.report.validation_requirements == ()
    assert result.report.hazards == ()
    assert {
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    } >= {
        ("actor_id", "l_energy"),
        ("site_id", "ocheong_plant_1"),
        ("allocation_method", "physical_allocation"),
        ("line_a_mass_ton", 50000),
        ("line_b_mass_ton", 20000),
        ("line_c_mass_ton", 30000),
        ("total_electricity_mwh", 6400),
        ("total_lng_nm3", 150000),
        ("dqr", "High"),
    }


def test_tier0_physical_allocation_creates_receipt_and_projection():
    result = run_tier0_physical_allocation_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "l_energy_own_emission_tco2e": 9999,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_tier0_physical_allocation_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.tier0_physical_allocation.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(TIER0_PHYSICAL_ALLOCATION_SCENARIO),
        TIER0_PHYSICAL_ALLOCATION_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.calculated_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
