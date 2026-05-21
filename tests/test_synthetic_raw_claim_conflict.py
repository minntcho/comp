from comp.compiler_tool import evidence_witness_fingerprint
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.synthetic_raw_claim_conflict.scenario import (
    ALIAS_BINDING_ID,
    EMAIL_ELECTRICITY_CLAIM_ID,
    EMS_ELECTRICITY_CLAIM_ID,
    EXPECTED_HAZARD_IDS,
    EXPECTED_OPEN_OBLIGATION_IDS,
    PERIOD_BINDING_ID,
    RAW_CLAIM_CONFLICT_SCENARIO,
    UNIT_CONVERSION_BINDING_ID,
    raw_conflict_hypothesis,
    run_raw_claim_conflict_scenario,
)


def test_raw_claim_conflict_keeps_source_candidates_separate():
    hypothesis = raw_conflict_hypothesis()
    result = run_raw_claim_conflict_scenario()

    assert tuple(
        (claim.field, claim.value, claim.origin)
        for claim in hypothesis.claims
    ) == (
        ("site_id", "OCH-01", "llm_extractor_candidate"),
        ("period", "2025-03", "llm_extractor_candidate"),
        (
            "electricity",
            {"amount": 6.4, "unit": "GWh", "source": "email"},
            "llm_extractor_candidate",
        ),
        (
            "electricity",
            {"amount": 6.1, "unit": "GWh", "source": "ems"},
            "parser_candidate",
        ),
    )
    assert {
        (claim.claim_id, claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    } == {
        (EMAIL_ELECTRICITY_CLAIM_ID, "email_electricity_mwh", 6400, "MWh"),
        (EMS_ELECTRICITY_CLAIM_ID, "ems_electricity_mwh", 6100, "MWh"),
    }
    assert "electricity_mwh" not in {
        claim.field
        for claim in result.report.checked_claims
    }
    assert "electricity_mwh" not in {
        claim.field
        for claim in result.report.derived_claims
    }


def test_raw_claim_conflict_binds_context_but_blocks_winner_selection():
    result = run_raw_claim_conflict_scenario()

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
            PERIOD_BINDING_ID,
            "reporting-period:2025-03",
            "period_policy",
        ),
        (
            UNIT_CONVERSION_BINDING_ID,
            "unit-conversion:GWh_to_MWh",
            "unit_conversion",
        ),
    )
    assert tuple(
        (claim.field, claim.reason)
        for claim in result.report.failed_claims
    ) == (
        ("electricity_mwh", "source_value_conflict"),
    )
    assert result.report.status == "blocked"


def test_raw_claim_conflict_opens_obligation_and_blocks_receipt():
    result = run_raw_claim_conflict_scenario()

    assert result.preparation.package.open_obligation_ids == EXPECTED_OPEN_OBLIGATION_IDS
    assert result.preparation.package.hazard_ids == EXPECTED_HAZARD_IDS
    assert result.preparation.decision.status == "hold"
    assert result.preparation.receipt is None
    assert result.projection is None


def test_raw_claim_conflict_preserves_all_witness_fingerprints():
    result = run_raw_claim_conflict_scenario()

    assert tuple(witness.witness_id for witness in result.report.evidence_witnesses) == (
        "w-email-electricity-march",
        "w-ems-electricity-march",
        "w-site-alias-policy",
        "w-reporting-period-policy",
        "w-unit-conversion-policy",
    )
    assert result.preparation.package.dependency_fingerprints == tuple(
        evidence_witness_fingerprint(witness)
        for witness in result.report.evidence_witnesses
    )


def test_raw_claim_conflict_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "synthetic.raw_claim_conflict.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(RAW_CLAIM_CONFLICT_SCENARIO),
        RAW_CLAIM_CONFLICT_SCENARIO.contract,
    )
