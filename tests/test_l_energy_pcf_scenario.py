from tests.domain_scenarios.assertions import assert_receipt_trace
from comp.compiler_tool import active_retrieval_query_policies
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.l_energy_pcf_governance.fixtures import profile
from tests.domain_scenarios.l_energy_pcf_governance.expected import (
    EXPECTED_DERIVED_CLAIM_IDS,
    EXPECTED_FORMULA_IDS,
    EXPECTED_PROJECTION,
    EXPECTED_SOURCE_REFS,
    EXPECTED_TRACE_IDS,
)
from tests.domain_scenarios.l_energy_pcf_governance.scenario import (
    SCENARIO as L_ENERGY_SCENARIO,
    run_l_energy_pcf_governance_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


def test_l_energy_pcf_governance_scenario_is_registered_with_source_refs():
    scenarios = registered_scenarios()

    assert "l_energy_pcf_governance.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert L_ENERGY_SCENARIO.source_refs == EXPECTED_SOURCE_REFS
    assert L_ENERGY_SCENARIO.contract.must_commit is True


def test_l_energy_pcf_governance_scenario_reproduces_platform_summary():
    result = run_l_energy_pcf_governance_scenario()

    assert result.scenario_id == "l_energy_pcf_governance.v1"
    assert result.report.status == "accepted"
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION


def test_l_energy_pcf_governance_scenario_resolves_energy_factor_through_retrieval():
    result = run_l_energy_pcf_governance_scenario()

    assert "resolver_tasks_from_report" in result.resolver_steps
    assert "profile_active_retrieval_policy" in result.resolver_steps
    assert "reference_retrieval:embedding_stub:factor" in result.resolver_steps
    assert tuple(
        obligation.kind for obligation in result.report.resolved_obligations
    ) == ("reference_search_required", "calculation_blocked")

    candidate_ids = tuple(
        candidate.candidate_id for candidate in result.report.reference_candidates
    )
    assert candidate_ids == (
        "embedding_stub:factor:idx-l-energy-electricity-mwh-2025",
        "embedding_stub:factor:idx-l-energy-electricity-mwh-2024",
    )
    assert all(
        candidate.authority == "candidate_only"
        for candidate in result.report.reference_candidates
    )

    electricity_binding = next(
        binding
        for binding in result.report.reference_bindings
        if binding.binding_id == "bind:pcf:electricity_factor"
    )
    assert (
        electricity_binding.selected_candidate_id
        == "embedding_stub:factor:idx-l-energy-electricity-mwh-2025"
    )
    assert tuple(
        (rejected.reference_id, rejected.reason)
        for rejected in electricity_binding.rejected_candidates
    ) == (
        ("platform.factor.electricity_mwh_2024", "attribute_mismatch:valid_period"),
    )

    own_emission_claim = next(
        claim
        for claim in result.report.derived_claims
        if claim.claim_id == "l-energy:own_emission_tco2e"
    )
    assert own_emission_claim.origin == "calculated"
    assert own_emission_claim.trace.reference_binding_ids == (
        "bind:pcf:electricity_factor",
    )


def test_l_energy_pcf_governance_pins_retrieval_policy_in_profile():
    scenario_profile = profile()

    assert scenario_profile.active_retrieval_policy_ids == (
        "l-energy-pcf-retrieval-query-policy-v1",
    )
    assert tuple(
        policy.policy_id
        for policy in active_retrieval_query_policies(scenario_profile)
    ) == ("l-energy-pcf-retrieval-query-policy-v1",)


def test_l_energy_pcf_governance_scenario_preserves_actor_receipt_trace():
    result = run_scenario(L_ENERGY_SCENARIO)

    assert_scenario_contract(result, L_ENERGY_SCENARIO.contract)
    assert result.preparation.package.open_obligation_ids == ()
    assert result.preparation.package.hazard_ids == ()
    assert tuple(claim.claim_id for claim in result.report.derived_claims) == (
        EXPECTED_DERIVED_CLAIM_IDS
    )
    assert_receipt_trace(
        result,
        derived_claim_ids=EXPECTED_DERIVED_CLAIM_IDS,
        calculation_trace_ids=EXPECTED_TRACE_IDS,
        formula_ids=EXPECTED_FORMULA_IDS,
    )


def test_l_energy_pcf_governance_scenario_exports_targeted_viewer_payload():
    exported = run_l_energy_pcf_governance_scenario().to_dict()

    assert exported["scenario_id"] == "l_energy_pcf_governance.v1"
    assert exported["commit"]["governance_status"] == "commit"
    assert exported["projection"] == EXPECTED_PROJECTION
    assert len(exported["report"]["derived_claims"]) == len(
        EXPECTED_DERIVED_CLAIM_IDS
    )
