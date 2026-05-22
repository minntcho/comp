import pytest

from comp.compiler_tool import (
    ValidationReport,
    ValidationRequirement,
    CanonicalReference,
    ReferenceOption,
    RejectedReferenceOption,
    SemanticJudgment,
    SemanticJudgmentRequirement,
    apply_semantic_judgments,
)


def test_reference_candidate_is_candidate_only_authority():
    candidate = ReferenceOption(
        candidate_id="cand-kr-grid-2024",
        reference_id="factor.kr_grid.2024",
        reference_type="emission_factor",
        retrieval_method="embedding",
        retrieval_score=0.91,
        source="reference_db",
        witness_ids=("span-amount",),
    )

    assert candidate.authority == "candidate_only"
    assert candidate.can_authorize_calculation is False

    report = ValidationReport(
        status="review_required",
        reference_options=(candidate,),
    )

    assert report.reference_options == (candidate,)
    assert report.canonical_references == ()


def test_reference_candidate_cannot_claim_binding_authority():
    with pytest.raises(ValueError, match="candidate_only"):
        ReferenceOption(
            candidate_id="cand-1",
            reference_id="factor.kr_grid.2024",
            reference_type="emission_factor",
            retrieval_method="embedding",
            authority="canonical_binding",
        )


def test_reference_binding_records_selector_and_rejected_candidates():
    rejected = RejectedReferenceOption(
        candidate_id="cand-residual-mix",
        reference_id="factor.kr_residual_mix.2024",
        reason="method_mismatch",
        selector_rule_id="ghg.factor_selector.v1",
    )
    binding = CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.kr_grid.2024",
        reference_type="emission_factor",
        selected_candidate_id="cand-kr-grid-2024",
        selector_rule_id="ghg.factor_selector.v1",
        source_witness_ids=("span-amount", "factor-row-17"),
        rejected_candidates=(rejected,),
    )

    assert binding.authority == "canonical_binding"
    assert binding.can_authorize_calculation is True
    assert binding.rejected_candidates == (rejected,)

    report = ValidationReport(status="accepted", canonical_references=(binding,))

    assert report.canonical_references == (binding,)
    assert report.reference_options == ()


def test_reference_binding_cannot_be_downgraded_to_candidate_authority():
    with pytest.raises(ValueError, match="canonical_binding"):
        CanonicalReference(
            binding_id="bind-1",
            claim_id="hyp-1:amount",
            reference_id="factor.kr_grid.2024",
            reference_type="emission_factor",
            authority="candidate_only",
        )


def test_semantic_judgment_application_preserves_reference_artifacts():
    candidate = ReferenceOption(
        candidate_id="cand-kr-grid-2024",
        reference_id="factor.kr_grid.2024",
        reference_type="emission_factor",
        retrieval_method="embedding",
    )
    binding = CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.kr_grid.2024",
        reference_type="emission_factor",
        selected_candidate_id=candidate.candidate_id,
        selector_rule_id="ghg.factor_selector.v1",
    )
    obligation = ValidationRequirement(
        kind="semantic_judgment_required",
        field="scope2_method",
        reason="semantic_support_required",
        obligation_id="obl-scope2",
        semantic_requirement=SemanticJudgmentRequirement(
            question="Does the span support market-based Scope 2?",
            claim_id="hyp-1:scope2_method",
            evidence_span_ids=("span-17",),
            rubric_id="ghg.scope2_method.v1",
            acceptable_verdicts=("supports", "refutes", "ambiguous"),
        ),
    )
    report = ValidationReport(
        status="review_required",
        validation_requirements=(obligation,),
        reference_options=(candidate,),
        canonical_references=(binding,),
    )

    updated = apply_semantic_judgments(
        report,
        [
            SemanticJudgment(
                judgment_id="judgment-1",
                obligation_id="obl-scope2",
                verdict="supports",
                rubric_id="ghg.scope2_method.v1",
                judge="llm/test",
                cited_span_ids=("span-17",),
                rationale="Fixture judgment.",
            )
        ],
        available_span_ids=("span-17",),
    )

    assert updated.reference_options == (candidate,)
    assert updated.canonical_references == (binding,)
