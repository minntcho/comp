import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from comp.compiler_tool import evidence_ref_fingerprint
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_acceptance.scenario import (
    ALIAS_BINDING_ID,
    ALLOCATED_ELECTRICITY_CLAIM_ID,
    ALLOCATION_SUPPORT_BINDING_ID,
    ALLOCATION_SHARE_CLAIM_ID,
    ELECTRICITY_MWH_CLAIM_ID,
    EXPECTED_PROJECTION,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO,
    UNIT_CONVERSION_BINDING_ID,
    raw_claim_hypothesis,
    run_raw_claim_hypothesis_acceptance_scenario,
)


def test_raw_claim_acceptance_promotes_only_canonical_checked_claims():
    hypothesis = raw_claim_hypothesis()
    result = run_raw_claim_hypothesis_acceptance_scenario()

    assert all(
        claim.origin == "llm_extractor_candidate"
        for claim in hypothesis.claims
    )
    assert ("site_id", "OCH-01") not in {
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    }
    assert {
        (claim.field, claim.value, claim.origin)
        for claim in result.report.checked_claims
    } >= {
        ("site_id", "ocheong_plant_1", "site_alias_binding"),
        ("period", "2025-03", "reporting_period_policy"),
        ("electricity_gwh", 6.4, "raw_candidate_with_unit_policy"),
        ("line_a_mass_ton", 50000, "physical_allocation_support"),
        ("total_line_mass_ton", 100000, "physical_allocation_support"),
    }
    assert result.report.failed_claims == ()
    assert result.report.obligations == ()
    assert result.report.hazards == ()


def test_raw_claim_acceptance_binds_alias_unit_and_allocation_support():
    result = run_raw_claim_hypothesis_acceptance_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (
            ALIAS_BINDING_ID,
            "site-alias:OCH-01->ocheong_plant_1",
            "site_alias",
        ),
        (
            UNIT_CONVERSION_BINDING_ID,
            "unit-conversion:GWh_to_MWh",
            "unit_conversion",
        ),
        (
            ALLOCATION_SUPPORT_BINDING_ID,
            "physical-allocation-support:line_a_mass_share",
            "physical_allocation_support",
        ),
    )
    assert tuple(item.kind for item in result.report.resolved_obligations) == (
        "site_alias_resolved",
        "unit_conversion_policy_applied",
        "period_validated",
        "physical_allocation_support_validated",
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        ALIAS_BINDING_ID,
        UNIT_CONVERSION_BINDING_ID,
        ALLOCATION_SUPPORT_BINDING_ID,
    )


def test_raw_claim_acceptance_calculates_canonical_values():
    result = run_raw_claim_hypothesis_acceptance_scenario()

    assert tuple(
        (claim.claim_id, claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    ) == (
        (ELECTRICITY_MWH_CLAIM_ID, "electricity_mwh", 6400, "MWh"),
        (ALLOCATION_SHARE_CLAIM_ID, "allocation_share", 0.5, None),
        (
            ALLOCATED_ELECTRICITY_CLAIM_ID,
            "allocated_electricity_mwh",
            3200,
            "MWh",
        ),
    )
    assert _trace_step_value(
        result,
        ELECTRICITY_MWH_CLAIM_ID,
        "convert-gwh-to-mwh",
    ) == 6400
    assert _trace_step_value(
        result,
        ALLOCATION_SHARE_CLAIM_ID,
        "line-a-allocation-share",
    ) == 0.5
    assert _trace_step_value(
        result,
        ALLOCATED_ELECTRICITY_CLAIM_ID,
        "allocated-electricity-mwh",
    ) == 3200


def test_raw_claim_acceptance_creates_receipt_and_projection():
    result = run_raw_claim_hypothesis_acceptance_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION
    assert result.preparation.receipt.citations.dependency_fingerprints == tuple(
        evidence_ref_fingerprint(witness)
        for witness in result.report.evidence_witnesses
    )

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "electricity_mwh": 9999,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_raw_claim_acceptance_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "synthetic.raw_claim_hypothesis_acceptance.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO),
        RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO.contract,
    )


def _trace_step_value(result, claim_id, step_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            for step in claim.trace.steps:
                if step.step_id == step_id:
                    return step.output_value
    raise AssertionError(f"missing step {step_id!r} for derived claim {claim_id!r}")
