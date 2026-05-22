from comp.compiler_tool import evidence_ref_fingerprint
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_gate.scenario import (
    EXPECTED_HAZARD_IDS,
    EXPECTED_OPEN_OBLIGATION_IDS,
    RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO,
    raw_claim_hypothesis,
    run_raw_claim_hypothesis_gate_scenario,
)


def test_raw_claim_hypotheses_are_candidates_not_authority():
    hypothesis = raw_claim_hypothesis()
    result = run_raw_claim_hypothesis_gate_scenario()

    assert tuple(
        (claim.field, claim.value, claim.origin)
        for claim in hypothesis.claims
    ) == (
        ("site_id", "OCH-01", "llm_extractor_candidate"),
        ("period", "2025-03", "llm_extractor_candidate"),
        (
            "electricity",
            {"amount": 6.4, "unit": "GWh"},
            "llm_extractor_candidate",
        ),
        ("allocation_share", 0.5, "llm_extractor_candidate"),
    )
    assert result.report.checked_claims == ()
    assert result.report.canonical_references == ()
    assert result.report.calculated_claims == ()


def test_raw_evidence_refs_are_preserved_and_fingerprinted():
    result = run_raw_claim_hypothesis_gate_scenario()

    assert tuple(
        (witness.witness_id, witness.source, witness.span, witness.text)
        for witness in result.report.evidence_refs
    ) == (
        (
            "w-email-electricity-march",
            "email:synthetic-pcf-smoke:001",
            "body[0:82]",
            "March electricity was 6.4 GWh for OCH-01, and Line A used about half.",
        ),
    )
    assert result.preparation.package.dependency_fingerprints == tuple(
        evidence_ref_fingerprint(witness)
        for witness in result.report.evidence_refs
    )


def test_raw_claim_gate_opens_obligations_and_blocks_receipt():
    result = run_raw_claim_hypothesis_gate_scenario()

    assert result.report.status == "blocked"
    assert (
        result.preparation.package.open_obligation_ids
        == EXPECTED_OPEN_OBLIGATION_IDS
    )
    assert result.preparation.package.hazard_ids == EXPECTED_HAZARD_IDS
    assert result.preparation.decision.status == "hold"
    assert result.preparation.receipt is None
    assert result.projection is None


def test_raw_claim_gate_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "synthetic.raw_claim_hypothesis_gate.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO),
        RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO.contract,
    )
