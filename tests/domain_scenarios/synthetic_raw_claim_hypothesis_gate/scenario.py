from __future__ import annotations

from comp import SubjectRef
from comp.compiler_tool import (
    ClaimHypothesis,
    CompileReport,
    EvidenceWitness,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ProofObligation,
    evidence_witness_fingerprint,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "synthetic.raw_claim_hypothesis_gate.v1"
SUBJECT_ID = "case:synthetic-raw-claim-hypothesis-gate"
PUBLIC_ROW_ID = "public-row:synthetic-raw-claim-hypothesis-gate"
PROJECTION_ID = "synthetic-raw-claim-hypothesis-gate"
PROFILE_ID = "profile:synthetic-raw-claim-hypothesis-gate:v1"

WITNESS_ID = "w-email-electricity-march"
EMAIL_SOURCE = "email:synthetic-pcf-smoke:001"
EMAIL_SPAN = "body[0:82]"
EMAIL_TEXT = (
    "March electricity was 6.4 GWh for OCH-01, and Line A used about half."
)

EXPECTED_OPEN_OBLIGATION_IDS = (
    "raw-claim-gate:site_alias:unresolved",
    "raw-claim-gate:unit_conversion:gwh_to_mwh_missing",
    "raw-claim-gate:period:mismatch",
    "raw-claim-gate:allocation_share:physical_support_missing",
)
EXPECTED_HAZARD_IDS = (
    "hazard:site_alias_unresolved:site_id:review",
    "hazard:unit_conversion_policy_missing:electricity_mwh:block",
    "hazard:period_mismatch:period:review",
    "hazard:physical_allocation_support_missing:allocation_share:block",
)

RESOLVER_STEPS = (
    "llm_extractor_candidate_fixture",
    "evidence_witness_fingerprint",
    "candidate_authority_gate",
    "site_alias_unresolved",
    "unit_conversion_policy_absent",
    "period_mismatch_detected",
    "allocation_share_physical_support_absent",
    "prepare_commit",
    "receipt_blocked_by_open_obligations",
    "oracle_source_to_truth_map_excluded",
)


def raw_claim_hypothesis() -> InterpretationHypothesis:
    return InterpretationHypothesis(
        hypothesis_id=SUBJECT_ID,
        subject_id=SUBJECT_ID,
        claims=(
            ClaimHypothesis(
                field="site_id",
                value="OCH-01",
                witness_id=WITNESS_ID,
                origin="llm_extractor_candidate",
            ),
            ClaimHypothesis(
                field="period",
                value="2025-03",
                witness_id=WITNESS_ID,
                origin="llm_extractor_candidate",
            ),
            ClaimHypothesis(
                field="electricity",
                value={"amount": 6.4, "unit": "GWh"},
                witness_id=WITNESS_ID,
                origin="llm_extractor_candidate",
            ),
            ClaimHypothesis(
                field="allocation_share",
                value=0.5,
                witness_id=WITNESS_ID,
                origin="llm_extractor_candidate",
            ),
        ),
        witnesses=_evidence_witnesses(),
    )


def run_raw_claim_hypothesis_gate_scenario() -> DomainScenarioResult:
    report = raw_claim_hypothesis_gate_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
        dependency_fingerprints=(
            evidence_witness_fingerprint(report.evidence_witnesses[0]),
        ),
    )
    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=None,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def raw_claim_hypothesis_gate_report() -> CompileReport:
    hypothesis = raw_claim_hypothesis()
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=hypothesis.witnesses,
            failed_claims=_failed_claims(),
            obligations=_open_obligations(),
            hazards=_hazards(),
            can_project_public_row=False,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id=WITNESS_ID,
            field="raw_email",
            source=EMAIL_SOURCE,
            span=EMAIL_SPAN,
            text=EMAIL_TEXT,
        ),
    )


def _failed_claims() -> tuple[FailedClaim, ...]:
    return (
        FailedClaim(
            field="site_id",
            value="OCH-01",
            reason="site_alias_unresolved",
            origin="llm_extractor_candidate",
            witness_id=WITNESS_ID,
        ),
        FailedClaim(
            field="period",
            value="2025-03",
            reason="period_mismatch",
            origin="llm_extractor_candidate",
            witness_id=WITNESS_ID,
        ),
        FailedClaim(
            field="electricity_mwh",
            value={"source_amount": 6.4, "source_unit": "GWh"},
            reason="unit_conversion_policy_missing",
            origin="llm_extractor_candidate",
            witness_id=WITNESS_ID,
        ),
        FailedClaim(
            field="allocation_share",
            value=0.5,
            reason="physical_allocation_support_missing",
            origin="llm_extractor_candidate",
            witness_id=WITNESS_ID,
        ),
    )


def _open_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="resolve_site_identity",
            field="site_id",
            reason="site_alias_unresolved",
            obligation_id=EXPECTED_OPEN_OBLIGATION_IDS[0],
        ),
        ProofObligation(
            kind="unit_conversion_policy_required",
            field="electricity_mwh",
            reason="gwh_to_mwh_conversion_policy_missing",
            obligation_id=EXPECTED_OPEN_OBLIGATION_IDS[1],
        ),
        ProofObligation(
            kind="find_context",
            field="period",
            reason="period_mismatch",
            obligation_id=EXPECTED_OPEN_OBLIGATION_IDS[2],
        ),
        ProofObligation(
            kind="physical_allocation_support_required",
            field="allocation_share",
            reason="line_mass_or_residence_time_support_missing",
            obligation_id=EXPECTED_OPEN_OBLIGATION_IDS[3],
        ),
    )


def _hazards() -> tuple[Hazard, ...]:
    return (
        Hazard(kind="site_alias_unresolved", field="site_id", severity="review"),
        Hazard(
            kind="unit_conversion_policy_missing",
            field="electricity_mwh",
            severity="block",
        ),
        Hazard(kind="period_mismatch", field="period", severity="review"),
        Hazard(
            kind="physical_allocation_support_missing",
            field="allocation_share",
            severity="block",
        ),
    )


RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic raw ClaimHypothesis gate",
    run=run_raw_claim_hypothesis_gate_scenario,
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=False,
        required_open_obligation_ids=EXPECTED_OPEN_OBLIGATION_IDS,
        required_hazard_ids=EXPECTED_HAZARD_IDS,
    ),
)


__all__ = [
    "EXPECTED_HAZARD_IDS",
    "EXPECTED_OPEN_OBLIGATION_IDS",
    "RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO",
    "SCENARIO_ID",
    "raw_claim_hypothesis",
    "raw_claim_hypothesis_gate_report",
    "run_raw_claim_hypothesis_gate_scenario",
]
