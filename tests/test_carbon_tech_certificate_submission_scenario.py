import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.carbon_tech_certificate_submission import (
    CARBON_TECH_CERTIFICATE_SCENARIO,
    CERTIFICATE_BOUNDARY_OBLIGATION_ID,
    CERTIFICATE_FACTOR_BINDING_ID,
    EXPECTED_PROJECTION,
    FINAL_EMISSION_CLAIM_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    run_carbon_tech_certificate_submission_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_carbon_certificate_calculates_emission_from_certificate_factor():
    result = run_carbon_tech_certificate_submission_scenario()

    trace = _trace_for(result, FINAL_EMISSION_CLAIM_ID)
    steps = {step.step_id: step.output_value for step in trace.steps}

    assert steps == {
        "certificate-emission-raw-tco2e": 13389.75,
        "rounded-certificate-emission-tco2e": 13390,
    }
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    ) == (("carbon_tech_final_emission_tco2e", 13390, "tCO2e"),)


def test_carbon_certificate_binds_certificate_factor_and_metadata():
    result = run_carbon_tech_certificate_submission_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (
            CERTIFICATE_FACTOR_BINDING_ID,
            "platform.factor.carbon_tech_certificate_per_ton",
            "certificate_factor",
        ),
    )
    assert {
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    } >= {
        ("submission_type", "certificate"),
        ("certificate_boundary", "Cradle-to-Gate"),
        ("dqr", "Medium"),
        ("production_ton", 8250),
        ("activity_input_mode", "certificate_only"),
    }
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        CERTIFICATE_FACTOR_BINDING_ID,
    )


def test_carbon_certificate_boundary_is_resolved_without_activity_inputs():
    result = run_carbon_tech_certificate_submission_scenario()

    assert result.report.status == "accepted"
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert tuple(
        (obligation.kind, obligation.field, obligation.reason)
        for obligation in result.report.resolved_obligations
    ) == (
        (
            "certificate_boundary_supported",
            "certificate_boundary",
            "supports_cradle_to_gate",
        ),
    )
    assert CERTIFICATE_BOUNDARY_OBLIGATION_ID in (
        result.preparation.receipt.citations.resolved_obligation_ids
    )
    assert result.preparation.receipt.citations.semantic_judgment_ids == ()
    assert "activity_electricity_mwh" not in tuple(
        claim.field for claim in result.report.checked_claims
    )
    assert "activity_lng_nm3" not in tuple(
        claim.field for claim in result.report.checked_claims
    )
    assert tuple(
        binding.reference_type for binding in result.report.reference_bindings
    ) == ("certificate_factor",)


def test_carbon_certificate_creates_receipt_and_projection():
    result = run_carbon_tech_certificate_submission_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "carbon_tech_final_emission_tco2e": 9999,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_carbon_certificate_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.carbon_tech_certificate_submission.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(CARBON_TECH_CERTIFICATE_SCENARIO),
        CARBON_TECH_CERTIFICATE_SCENARIO.contract,
    )


def _trace_for(result, claim_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            return claim.trace
    raise AssertionError(f"missing derived claim: {claim_id}")
