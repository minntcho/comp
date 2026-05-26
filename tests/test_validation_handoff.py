import pytest


def test_validation_handoff_builds_hypothesis_from_selected_contract_claims():
    from comp.compiler_tool import ClaimCandidate, EvidenceRef, InterpretationHypothesis
    from comp.policy import SelectedValidationContract
    from comp.runtime import ValidationHandoff, ValidationHandoffClaim

    contract = SelectedValidationContract(
        contract_id="selected-contract:run-1",
        policy_profile_id="profile:strict-public",
        ledger_id="ledger:run-1",
        basis="policy resolver finalized validation handoff",
        selected_decision_ids=("decision:plant->site",),
        selected_decision_targets=(("decision:plant->site", "field:site"),),
        projection_candidate_decision_ids=("decision:fuel_used->amount",),
        ledger_digest="digest:ledger-run-1",
    )
    claim = ClaimCandidate(
        field="site",
        value="Plant A",
        witness_id="w-plant",
        origin="policy_handoff",
    )
    witness = EvidenceRef(
        witness_id="w-plant",
        field="site",
        source="source:invoice-1",
        span="Plant A",
        text="Plant A used 1200 L diesel",
    )

    handoff = ValidationHandoff(
        handoff_id="handoff:run-1",
        contract=contract,
        hypothesis_id="hypothesis:run-1",
        subject_id="subject:facility-1",
        claims=(
            ValidationHandoffClaim(
                decision_id="decision:plant->site",
                claim=claim,
            ),
        ),
        witnesses=(witness,),
    )

    hypothesis = handoff.to_interpretation_hypothesis()

    assert isinstance(hypothesis, InterpretationHypothesis)
    assert hypothesis.hypothesis_id == "hypothesis:run-1"
    assert hypothesis.subject_id == "subject:facility-1"
    assert hypothesis.claims == (claim,)
    assert hypothesis.witnesses == (witness,)
    assert handoff.policy_profile_id == "profile:strict-public"
    assert handoff.ledger_id == "ledger:run-1"
    assert handoff.selected_decision_ids == ("decision:plant->site",)
    assert handoff.authorizes_public_projection is False
    assert not hasattr(handoff, "compile")
    assert not hasattr(handoff, "prepare_commit")
    assert not hasattr(handoff, "build_public_output_receipt")


def test_validation_handoff_rejects_claims_outside_selected_contract():
    from comp.compiler_tool import ClaimCandidate
    from comp.policy import SelectedValidationContract
    from comp.runtime import ValidationHandoff, ValidationHandoffClaim

    contract = SelectedValidationContract(
        contract_id="selected-contract:run-1",
        policy_profile_id="profile:strict-public",
        ledger_id="ledger:run-1",
        basis="policy resolver finalized validation handoff",
        selected_decision_ids=("decision:plant->site",),
        projection_candidate_decision_ids=("decision:fuel_used->amount",),
    )

    with pytest.raises(ValueError, match="not selected for validation handoff"):
        ValidationHandoff(
            handoff_id="handoff:run-1",
            contract=contract,
            hypothesis_id="hypothesis:run-1",
            subject_id="subject:facility-1",
            claims=(
                ValidationHandoffClaim(
                    decision_id="decision:fuel_used->amount",
                    claim=ClaimCandidate(field="amount", value=1200),
                ),
            ),
        )


def test_validation_handoff_rejects_claim_field_outside_selected_target():
    from comp.compiler_tool import ClaimCandidate
    from comp.policy import SelectedValidationContract
    from comp.runtime import ValidationHandoff, ValidationHandoffClaim

    contract = SelectedValidationContract(
        contract_id="selected-contract:run-1",
        policy_profile_id="profile:strict-public",
        ledger_id="ledger:run-1",
        basis="policy resolver finalized validation handoff",
        selected_decision_ids=("decision:plant->site",),
        selected_decision_targets=(("decision:plant->site", "field:site"),),
    )

    with pytest.raises(ValueError, match="claim field does not match selected target"):
        ValidationHandoff(
            handoff_id="handoff:run-1",
            contract=contract,
            hypothesis_id="hypothesis:run-1",
            subject_id="subject:facility-1",
            claims=(
                ValidationHandoffClaim(
                    decision_id="decision:plant->site",
                    claim=ClaimCandidate(field="amount", value=1200),
                ),
            ),
        )


def test_validation_handoff_requires_claims_for_each_selected_decision():
    from comp.compiler_tool import ClaimCandidate
    from comp.policy import SelectedValidationContract
    from comp.runtime import ValidationHandoff, ValidationHandoffClaim

    contract = SelectedValidationContract(
        contract_id="selected-contract:run-1",
        policy_profile_id="profile:strict-public",
        ledger_id="ledger:run-1",
        basis="policy resolver finalized validation handoff",
        selected_decision_ids=("decision:plant->site", "decision:unit->unit"),
    )

    with pytest.raises(ValueError, match="missing handoff claim"):
        ValidationHandoff(
            handoff_id="handoff:run-1",
            contract=contract,
            hypothesis_id="hypothesis:run-1",
            subject_id="subject:facility-1",
            claims=(
                ValidationHandoffClaim(
                    decision_id="decision:plant->site",
                    claim=ClaimCandidate(field="site", value="Plant A"),
                ),
            ),
        )
