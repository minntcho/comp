from comp import JudgmentState, SubjectRef
from comp.compiler_tool import (
    CheckedClaim,
    ValidationReport,
    ValidationRequirement,
    add_commit_preparation_facts,
    commit_preparation_to_facts,
    prepare_commit,
)


def test_commit_preparation_to_facts_records_package_decision_and_receipt():
    preparation = prepare_commit(
        ValidationReport(
            status="accepted",
            checked_claims=(
                CheckedClaim(
                    field="amount",
                    value=1200,
                    witness_id="span-amount",
                    origin="source_text",
                ),
            ),
        ),
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
        profile_id="esg-ghg-v1",
        semantic_judgment_ids=("judgment-scope2",),
    )

    subject = SubjectRef("draft", "facility-1")
    facts = commit_preparation_to_facts(preparation, subject)

    package_fact = _one(facts, "prov_edge", "commit_package")
    decision_fact = _one(facts, "prov_edge", "governance_decision")
    receipt_fact = _one(facts, "prov_edge", "commit_receipt")

    assert package_fact.value == "commit-package:facility-1"
    assert ("complete", True) in package_fact.meta
    assert ("checked_claim_fields", ("amount",)) in package_fact.meta
    assert ("semantic_judgment_ids", ("judgment-scope2",)) in package_fact.meta
    assert ("calculation_trace_ids", ()) in package_fact.meta
    assert ("open_obligation_ids", ()) in package_fact.meta
    assert ("hazard_ids", ()) in package_fact.meta

    assert decision_fact.value == "governance-decision:commit-package:facility-1"
    assert ("governance_status", "commit") in decision_fact.meta
    assert ("can_issue_commit_receipt", True) in decision_fact.meta

    assert receipt_fact.value == "public-row-1"
    assert receipt_fact.witness == "governance-decision:commit-package:facility-1"
    assert ("commit_package_id", "commit-package:facility-1") in receipt_fact.meta
    assert ("receipt_snapshot", preparation.receipt.barrier_snapshot) in receipt_fact.meta


def test_commit_preparation_to_facts_keeps_hold_visible_without_receipt_fact():
    preparation = prepare_commit(
        ValidationReport(
            status="accepted",
            obligations=(
                ValidationRequirement(
                    kind="reference_selection_required",
                    field="co2e_emission",
                    reason="ambiguous",
                    obligation_id="reference-selection:hyp-1:co2e_emission",
                ),
            ),
        ),
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    subject = SubjectRef("draft", "facility-1")
    facts = commit_preparation_to_facts(preparation, subject)

    decision_fact = _one(facts, "prov_edge", "governance_decision")
    receipt_facts = [fact for fact in facts if fact.key == "commit_receipt"]
    hazard_fact = _one(
        facts,
        "hazard_open",
        "commit_obligation:reference-selection:hyp-1:co2e_emission",
    )

    assert decision_fact.value == "governance-decision:commit-package:facility-1"
    assert ("governance_status", "hold") in decision_fact.meta
    package_fact = _one(facts, "prov_edge", "commit_package")
    assert (
        "open_obligation_ids",
        ("reference-selection:hyp-1:co2e_emission",),
    ) in package_fact.meta
    assert receipt_facts == []
    assert hazard_fact.value == "reference-selection:hyp-1:co2e_emission"


def test_add_commit_preparation_facts_updates_judgment_state_once():
    preparation = prepare_commit(
        ValidationReport(status="accepted"),
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
    )
    subject = SubjectRef("draft", "facility-1")
    state = JudgmentState()

    first_delta = add_commit_preparation_facts(state, preparation, subject)
    second_delta = add_commit_preparation_facts(state, preparation, subject)

    assert first_delta
    assert second_delta == set()
    assert state.version_of(subject) == 1


def _one(facts, tag, key):
    matches = [fact for fact in facts if fact.tag == tag and fact.key == key]
    assert len(matches) == 1
    return matches[0]
