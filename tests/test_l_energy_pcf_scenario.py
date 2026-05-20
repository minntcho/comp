from tests.domain_scenarios.assertions import assert_receipt_trace
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
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
