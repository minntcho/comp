from comp.compiler_tool import evidence_witness_fingerprint
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.synthetic_raw_claim_conflict_resolution.scenario import (
    CANONICAL_ELECTRICITY_CLAIM_ID,
    EMAIL_ELECTRICITY_CLAIM_ID,
    EMS_ELECTRICITY_CLAIM_ID,
    EXPECTED_PROJECTION,
    RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO,
    RESOLUTION_BINDING_ID,
    run_raw_claim_conflict_resolution_scenario,
)


def test_raw_claim_conflict_resolution_preserves_conflicting_sources():
    result = run_raw_claim_conflict_resolution_scenario()

    assert {
        (claim.claim_id, claim.field, claim.value, claim.unit)
        for claim in result.report.derived_claims
    } >= {
        (EMAIL_ELECTRICITY_CLAIM_ID, "email_electricity_mwh", 6400, "MWh"),
        (EMS_ELECTRICITY_CLAIM_ID, "ems_electricity_mwh", 6100, "MWh"),
        (CANONICAL_ELECTRICITY_CLAIM_ID, "electricity_mwh", 6100, "MWh"),
    }
    assert tuple(
        (claim.field, claim.value, claim.origin)
        for claim in result.report.checked_claims
        if claim.field == "selected_electricity_source"
    ) == (
        (
            "selected_electricity_source",
            "ems",
            "source_conflict_resolution_evidence",
        ),
    )


def test_raw_claim_conflict_resolution_cites_resolution_binding_for_winner():
    result = run_raw_claim_conflict_resolution_scenario()

    canonical = next(
        claim
        for claim in result.report.derived_claims
        if claim.claim_id == CANONICAL_ELECTRICITY_CLAIM_ID
    )

    assert RESOLUTION_BINDING_ID in canonical.trace.reference_binding_ids
    assert tuple(
        binding.binding_id
        for binding in result.report.reference_bindings
        if binding.reference_type == "source_conflict_resolution"
    ) == (RESOLUTION_BINDING_ID,)
    assert tuple(
        obligation.kind
        for obligation in result.report.resolved_obligations
        if obligation.field == "electricity_mwh"
    ) == (
        "unit_conversion_policy_applied",
        "source_conflict_resolved",
    )


def test_raw_claim_conflict_resolution_commits_and_projects_selected_value():
    result = run_raw_claim_conflict_resolution_scenario()

    assert result.report.status == "accepted"
    assert result.report.failed_claims == ()
    assert result.report.hazards == ()
    assert result.preparation.package.open_obligation_ids == ()
    assert result.preparation.package.hazard_ids == ()
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION


def test_raw_claim_conflict_resolution_fingerprints_resolution_witness():
    result = run_raw_claim_conflict_resolution_scenario()

    assert tuple(witness.witness_id for witness in result.report.evidence_witnesses) == (
        "w-email-electricity-march",
        "w-ems-electricity-march",
        "w-site-alias-policy",
        "w-reporting-period-policy",
        "w-unit-conversion-policy",
        "w-source-conflict-resolution",
    )
    assert result.preparation.package.dependency_fingerprints == tuple(
        evidence_witness_fingerprint(witness)
        for witness in result.report.evidence_witnesses
    )


def test_raw_claim_conflict_resolution_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "synthetic.raw_claim_conflict_resolution.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO),
        RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO.contract,
    )
