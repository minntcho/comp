import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.final_bottom_up_rollup import (
    CARBON_TECH_CHILD_BINDING_ID,
    C_PACK_CHILD_BINDING_ID,
    EXPECTED_PROJECTION,
    FINAL_BOTTOM_UP_ROLLUP_SCENARIO,
    KWH_INTENSITY_CLAIM_ID,
    L_MATERIALS_CHILD_BINDING_ID,
    PACK_INTENSITY_CLAIM_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    TIER0_CHILD_BINDING_ID,
    TOTAL_EMISSION_CLAIM_ID,
    run_final_bottom_up_rollup_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_final_bottom_up_rollup_calculates_total_and_intensities():
    result = run_final_bottom_up_rollup_scenario()

    assert (
        _trace_step_value(result, TOTAL_EMISSION_CLAIM_ID, "bottom-up-total-tco2e")
        == 199994
    )
    assert (
        _trace_step_value(result, PACK_INTENSITY_CLAIM_ID, "kg-co2e-per-pack")
        == 1999.94
    )
    assert (
        _trace_step_value(result, KWH_INTENSITY_CLAIM_ID, "kg-co2e-per-kwh")
        == 26.66
    )
    assert tuple(
        (claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    ) == (
        ("l_energy_total_emission_tco2e", 199994, "tCO2e"),
        ("kg_co2e_per_pack", 1999.94, "kgCO2e/pack"),
        ("kg_co2e_per_kwh", 26.66, "kgCO2e/kWh"),
    )


def test_final_bottom_up_rollup_binds_all_child_receipts():
    result = run_final_bottom_up_rollup_scenario()

    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in result.report.reference_bindings
    ) == (
        (
            TIER0_CHILD_BINDING_ID,
            "scenario:l_energy.tier0_physical_allocation.v1",
            "child_receipt",
        ),
        (
            C_PACK_CHILD_BINDING_ID,
            "scenario:l_energy.c_pack_yield_rollup.v1",
            "child_receipt",
        ),
        (
            CARBON_TECH_CHILD_BINDING_ID,
            "scenario:l_energy.carbon_tech_certificate_submission.v1",
            "child_receipt",
        ),
        (
            L_MATERIALS_CHILD_BINDING_ID,
            "scenario:l_energy.l_materials_composition_rollup.v1",
            "child_receipt",
        ),
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations.reference_binding_ids == (
        TIER0_CHILD_BINDING_ID,
        C_PACK_CHILD_BINDING_ID,
        CARBON_TECH_CHILD_BINDING_ID,
        L_MATERIALS_CHILD_BINDING_ID,
    )


def test_final_bottom_up_rollup_requires_authorized_child_paths():
    result = run_final_bottom_up_rollup_scenario()

    assert tuple(item.kind for item in result.report.resolved_obligations) == (
        "child_claims_accepted_or_proxy_authorized",
        "rollup_snapshot_created",
    )
    assert result.report.status == "accepted"
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert {
        (claim.field, claim.value)
        for claim in result.report.checked_claims
    } >= {
        ("actor_id", "l_energy"),
        ("pack_count", 100000),
        ("total_energy_gwh", 7.5),
        ("l_energy_own_emission_tco2e", 1695),
        ("c_pack_final_emission_tco2e", 10534),
        ("carbon_tech_final_emission_tco2e", 13390),
        ("l_materials_final_emission_tco2e", 174375),
        ("c_pack_dependency_kind", "proxy_authorized_child_rollup"),
    }


def test_final_bottom_up_rollup_creates_receipt_and_projection():
    result = run_final_bottom_up_rollup_scenario()

    assert result.preparation.package.complete is True
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION

    with pytest.raises(PublicOutputBlocked, match="value commitment mismatch"):
        build_public_output(
            {
                **EXPECTED_PROJECTION,
                "kg_co2e_per_kwh": 99.99,
            },
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=result.preparation.receipt,
        )


def test_final_bottom_up_rollup_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "l_energy.final_bottom_up_pcf_rollup.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(FINAL_BOTTOM_UP_ROLLUP_SCENARIO),
        FINAL_BOTTOM_UP_ROLLUP_SCENARIO.contract,
    )


def _trace_step_value(result, claim_id, step_id):
    for claim in result.report.derived_claims:
        if claim.claim_id == claim_id:
            for step in claim.trace.steps:
                if step.step_id == step_id:
                    return step.output_value
    raise AssertionError(f"missing step {step_id!r} for derived claim {claim_id!r}")
