from comp.compiler_tool import (
    ValidationReport,
    ValidationRequirement,
    SemanticJudgment,
    SemanticJudgmentRequirement,
    UncheckedArea,
    apply_semantic_judgments,
)


def _semantic_obligation():
    return ValidationRequirement(
        kind="semantic_judgment_required",
        field="scope2_method",
        reason="semantic_support_required",
        requirement_id="obl-scope2-method",
        claim_id="claim-scope2-method",
        semantic_requirement=SemanticJudgmentRequirement(
            question="Does the cited span support the claimed Scope 2 method?",
            claim_id="claim-scope2-method",
            evidence_span_ids=("span-17",),
            rubric_id="ghg-protocol-scope2-method-v1",
            acceptable_verdicts=("supports", "refutes", "ambiguous"),
            required_verdict="supports",
            allowed_judges=("human/reviewer", "llm/model@policy-v1"),
        ),
    )


def _judgment(**overrides):
    data = {
        "judgment_id": "judgment-1",
        "requirement_id": "obl-scope2-method",
        "verdict": "supports",
        "rubric_id": "ghg-protocol-scope2-method-v1",
        "judge": "llm/model@policy-v1",
        "cited_span_ids": ("span-17",),
        "rationale": "The cited wording supports the requested method.",
        "confidence": 0.82,
    }
    data.update(overrides)
    return SemanticJudgment(**data)


def test_semantic_judgment_model_set_is_exported():
    assert SemanticJudgmentRequirement is not None
    assert SemanticJudgment is not None
    assert apply_semantic_judgments is not None


def test_matching_semantic_judgment_discharges_obligation():
    obligation = _semantic_obligation()
    report = ValidationReport(status="review_required", validation_requirements=(obligation,))

    resolved = apply_semantic_judgments(
        report,
        (_judgment(),),
        available_span_ids=("span-17",),
    )

    assert resolved.status == "accepted"
    assert resolved.validation_requirements == ()
    assert resolved.resolved_validation_requirements == (obligation,)
    assert resolved.hazards == ()


def test_wrong_rubric_does_not_discharge_obligation():
    obligation = _semantic_obligation()
    report = ValidationReport(status="review_required", validation_requirements=(obligation,))

    resolved = apply_semantic_judgments(
        report,
        (_judgment(rubric_id="wrong-rubric"),),
        available_span_ids=("span-17",),
    )

    assert resolved.status == "review_required"
    assert resolved.validation_requirements == (obligation,)
    assert resolved.resolved_validation_requirements == ()


def test_unaccepted_or_non_required_verdict_does_not_discharge_obligation():
    obligation = _semantic_obligation()
    report = ValidationReport(status="review_required", validation_requirements=(obligation,))

    refuted = apply_semantic_judgments(
        report,
        (_judgment(verdict="refutes"),),
        available_span_ids=("span-17",),
    )
    unsupported = apply_semantic_judgments(
        report,
        (_judgment(verdict="not_sure"),),
        available_span_ids=("span-17",),
    )

    assert refuted.status == "review_required"
    assert refuted.validation_requirements == (obligation,)
    assert refuted.resolved_validation_requirements == ()
    assert unsupported.status == "review_required"
    assert unsupported.validation_requirements == (obligation,)
    assert unsupported.resolved_validation_requirements == ()


def test_unallowed_judge_or_missing_cited_span_does_not_discharge_obligation():
    obligation = _semantic_obligation()
    report = ValidationReport(status="review_required", validation_requirements=(obligation,))

    unallowed_judge = apply_semantic_judgments(
        report,
        (_judgment(judge="llm/unapproved"),),
        available_span_ids=("span-17",),
    )
    missing_span = apply_semantic_judgments(
        report,
        (_judgment(cited_span_ids=("span-missing",)),),
        available_span_ids=("span-17",),
    )

    assert unallowed_judge.validation_requirements == (obligation,)
    assert unallowed_judge.resolved_validation_requirements == ()
    assert missing_span.validation_requirements == (obligation,)
    assert missing_span.resolved_validation_requirements == ()


def test_conflicting_semantic_judgments_keep_obligation_open_and_add_hazard():
    obligation = _semantic_obligation()
    report = ValidationReport(status="review_required", validation_requirements=(obligation,))

    resolved = apply_semantic_judgments(
        report,
        (
            _judgment(judgment_id="judgment-supports", verdict="supports"),
            _judgment(judgment_id="judgment-refutes", verdict="refutes"),
        ),
        available_span_ids=("span-17",),
    )

    assert resolved.status == "review_required"
    assert resolved.validation_requirements == (obligation,)
    assert resolved.resolved_validation_requirements == ()
    assert len(resolved.hazards) == 1
    assert resolved.hazards[0].kind == "conflicting_semantic_judgment"
    assert resolved.hazards[0].field == "scope2_method"


def test_nonsemantic_obligations_do_not_reclassify_unchecked_report():
    obligation = ValidationRequirement(
        kind="define_rule_coverage",
        field="factor_period_compatibility",
        reason="missing_rule_coverage",
    )
    report = ValidationReport(
        status="unchecked",
        unchecked_areas=(
            UncheckedArea(
                field="factor_period_compatibility",
                reason="missing_rule_coverage",
            ),
        ),
        validation_requirements=(obligation,),
    )

    resolved = apply_semantic_judgments(report, ())

    assert resolved.status == "unchecked"
    assert resolved.validation_requirements == (obligation,)
    assert resolved.resolved_validation_requirements == ()
