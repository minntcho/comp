import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.alpha_invalid_allocation_rfi import (
    ALPHA_INVALID_ALLOCATION_SCENARIO,
    NORMALIZATION_SUGGESTION,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    RAW_MATERIAL_NAME,
    run_alpha_invalid_allocation_rfi_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_alpha_revenue_share_opens_methodological_failed_claim():
    result = run_alpha_invalid_allocation_rfi_scenario()

    assert result.report.status == "blocked"
    assert tuple(
        (claim.field, claim.value, claim.reason)
        for claim in result.report.failed_claims
    ) == (("allocation_method", "revenue_share", "economic_allocation_not_allowed"),)
    assert result.preparation.package.complete is False
    assert result.preparation.decision.status == "hold"


def test_alpha_revenue_share_requires_rolling_residence_time_context():
    result = run_alpha_invalid_allocation_rfi_scenario()

    assert tuple(
        (obligation.kind, obligation.field, obligation.reason)
        for obligation in result.report.validation_requirements
    ) == (
        (
            "find_context",
            "rolling_residence_time",
            "physical_allocation_parameter_required",
        ),
    )
    assert result.preparation.package.open_obligation_ids == (
        "alpha-metal:rolling_residence_time:physical_allocation_parameter_required",
    )


def test_alpha_normalization_suggestion_is_not_authoritative():
    result = run_alpha_invalid_allocation_rfi_scenario()

    assert RAW_MATERIAL_NAME == "알미늄 판넬"
    assert NORMALIZATION_SUGGESTION == "Aluminum Sheet"
    assert tuple(
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    ) == (("raw_material_name", RAW_MATERIAL_NAME),)
    assert "normalized_material_name" not in tuple(
        claim.field for claim in result.report.checked_claims
    )
    assert "Aluminum Sheet" not in tuple(
        claim.value for claim in result.report.checked_claims
    )


def test_alpha_invalid_allocation_cannot_create_receipt_or_projection():
    result = run_alpha_invalid_allocation_rfi_scenario()

    assert result.report.canonical_references == ()
    assert result.report.calculated_claims == ()
    assert result.preparation.receipt is None
    assert result.projection is None
    with pytest.raises(PublicOutputBlocked, match="public-output receipt"):
        build_public_output(
            {"raw_material_name": RAW_MATERIAL_NAME},
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
        )


def test_alpha_invalid_allocation_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.alpha_invalid_allocation_rfi.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(ALPHA_INVALID_ALLOCATION_SCENARIO),
        ALPHA_INVALID_ALLOCATION_SCENARIO.contract,
    )
