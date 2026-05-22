import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.steel_frame_proxy_assignment import (
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    PROXY_BINDING_ID,
    STEEL_FRAME_PROXY_SCENARIO,
    SUPPLIER_ABSENCE_OBLIGATION_ID,
    run_steel_frame_proxy_assignment_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_steel_frame_proxy_calculates_missing_mass_and_emission():
    result = run_steel_frame_proxy_assignment_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "missing-mass-ton": 1900,
        "proxy-emission-tco2e": 4750,
    }
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    ) == (
        ("missing_mass_ton", 1900, "ton"),
        ("steel_frame_final_emission_tco2e", 4750, "tCO2e"),
    )


def test_steel_frame_proxy_binds_proxy_factor_and_low_quality_metadata():
    result = run_steel_frame_proxy_assignment_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (PROXY_BINDING_ID, "platform.factor.steel_proxy_per_ton", "proxy_factor"),
    )
    assert ("proxy_quality", "Low") in tuple(
        (claim.field, claim.value) for claim in result.report.checked_claims
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        PROXY_BINDING_ID,
    )


def test_steel_frame_missing_supplier_context_is_explicit_but_not_blocking():
    result = run_steel_frame_proxy_assignment_scenario()

    assert result.report.status == "accepted"
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert tuple(
        (obligation.kind, obligation.field, obligation.reason)
        for obligation in result.report.resolved_obligations
    ) == (
        (
            "find_source_witness",
            "steel_frame_supplier_submission",
            "supplier_submission_absent",
        ),
        (
            "proxy_factor_required",
            "steel_frame_proxy_factor",
            "missing_supplier_evidence_requires_proxy",
        ),
    )
    assert result.preparation.package.open_obligation_ids == ()
    assert SUPPLIER_ABSENCE_OBLIGATION_ID in (
        result.preparation.receipt.citations.resolved_obligation_ids
    )


def test_steel_frame_proxy_creates_receipt_and_projection():
    result = run_steel_frame_proxy_assignment_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "steel_frame_final_emission_tco2e": 9999,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_steel_frame_proxy_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.steel_frame_proxy_assignment.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(STEEL_FRAME_PROXY_SCENARIO),
        STEEL_FRAME_PROXY_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
