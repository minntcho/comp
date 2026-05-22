import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.c_pack_yield_rollup import (
    ALPHA_CHILD_CLAIM_ID,
    C_PACK_YIELD_ROLLUP_SCENARIO,
    ELECTRICITY_BINDING_ID,
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    PROXY_DEPENDENCY_OBLIGATION_ID,
    STEEL_PROXY_CHILD_CLAIM_ID,
    run_c_pack_yield_rollup_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_c_pack_yield_rollup_calculates_required_input_and_final_emission():
    result = run_c_pack_yield_rollup_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "required-lower-tier-input-ton": 6300,
        "c-pack-own-emission-tco2e": 478,
        "lower-tier-rollup-tco2e": 10056,
        "final-emission-tco2e": 10534,
    }
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.calculated_claims
    ) == (
        ("required_lower_tier_input_ton", 6300, "ton"),
        ("c_pack_own_emission_tco2e", 478, "tCO2e"),
        ("lower_tier_rollup_tco2e", 10056, "tCO2e"),
        ("verified_primary_coverage", 0.698, None),
        ("proxy_coverage", 0.302, None),
        ("c_pack_final_emission_tco2e", 10534, "tCO2e"),
    )


def test_c_pack_rollup_preserves_child_claim_and_proxy_dependencies():
    result = run_c_pack_yield_rollup_scenario()

    final_trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)

    assert final_trace.input_claim_ids == (
        "c-pack:own_emission_tco2e",
        ALPHA_CHILD_CLAIM_ID,
        STEEL_PROXY_CHILD_CLAIM_ID,
    )
    assert {
        (claim.field, claim.value, claim.origin)
        for claim in result.report.checked_claims
    } >= {
        ("alpha_metal_final_emission_tco2e", 5306, "child_receipt"),
        ("steel_frame_final_emission_tco2e", 4750, "proxy_child_receipt"),
        ("steel_frame_dependency_kind", "proxy_assignment", "proxy_child_receipt"),
    }
    assert PROXY_DEPENDENCY_OBLIGATION_ID in (
        result.preparation.receipt.citations.resolved_obligation_ids
    )


def test_c_pack_rollup_binds_assembly_electricity_factor():
    result = run_c_pack_yield_rollup_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.canonical_references
    ) == (
        (ELECTRICITY_BINDING_ID, "platform.factor.electricity_mwh", "emission_factor"),
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        ELECTRICITY_BINDING_ID,
    )


def test_c_pack_rollup_creates_receipt_and_projection():
    result = run_c_pack_yield_rollup_scenario()

    assert result.report.status == "accepted"
    assert result.report.validation_requirements == ()
    assert result.report.hazards == ()
    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "c_pack_final_emission_tco2e": 9999,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_c_pack_yield_rollup_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.c_pack_yield_rollup.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(C_PACK_YIELD_ROLLUP_SCENARIO),
        C_PACK_YIELD_ROLLUP_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.calculated_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
