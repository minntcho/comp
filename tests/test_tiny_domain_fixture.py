from comp.compiler_tool import (
    ClaimCandidate,
    CompilerProfile,
    DomainPack,
    EvidenceRef,
    InterpretationHypothesis,
    JudgePolicy,
    ValidationRequirement,
    RuleFamily,
    SemanticJudgment,
    SemanticRubric,
    active_rule_families,
    apply_semantic_judgments,
    compile_with_profile,
    run_profile_rules,
)


SCOPE2_RUBRIC_ID = "fixture.ghg.scope2_method_support.v1"
SCOPE2_RULE_ID = "fixture.ghg.scope2_method_support_rule.v1"
JUDGE_POLICY_ID = "fixture.default_judge_policy.v1"


def _scope2_method_rule(claim, hypothesis, profile):
    if claim.field != "scope2_method":
        return ()
    rubric = profile.rubric(SCOPE2_RUBRIC_ID)
    judge_policy = profile.judge_policy()
    return (
        ValidationRequirement(
            kind="semantic_judgment_required",
            field=claim.field,
            reason="semantic_support_required",
            obligation_id=f"semantic:{claim.field}:{claim.witness_id}",
            claim_id=f"{hypothesis.hypothesis_id}:{claim.field}",
            semantic_requirement=rubric.requirement(
                question="Does the cited span support the claimed Scope 2 method?",
                claim_id=f"{hypothesis.hypothesis_id}:{claim.field}",
                evidence_span_ids=(claim.witness_id,),
                allowed_judges=judge_policy.allowed_judges,
            ),
        ),
    )


def _tiny_domain(*, known_fields=("scope2_method",), allowed_units=()):
    return DomainPack(
        domain_id="fixture-ghg",
        version="2026.1",
        known_fields=tuple(known_fields),
        allowed_units=tuple(allowed_units),
        rule_families=(
            RuleFamily(
                rule_id=SCOPE2_RULE_ID,
                required_rubric_ids=(SCOPE2_RUBRIC_ID,),
                evaluate=_scope2_method_rule,
                evaluator_id="fixture.ghg.scope2_method_support_rule.evaluator",
                implementation_version="2026.1",
            ),
            RuleFamily(rule_id="fixture.inactive_rule.v1"),
        ),
        rubrics=(
            SemanticRubric(
                rubric_id=SCOPE2_RUBRIC_ID,
                acceptable_verdicts=("supports", "refutes", "ambiguous"),
                required_verdict="supports",
            ),
        ),
        judge_policies=(
            JudgePolicy(
                judge_policy_id=JUDGE_POLICY_ID,
                allowed_judges=("human/reviewer", "llm/model@policy-v1"),
            ),
        ),
    )


def _profile(
    *,
    active_rule_ids=(SCOPE2_RULE_ID,),
    known_fields=("scope2_method",),
    allowed_units=(),
):
    return CompilerProfile(
        profile_id="fixture-ghg-profile",
        domain_packs=(
            _tiny_domain(known_fields=known_fields, allowed_units=allowed_units),
        ),
        active_rule_ids=active_rule_ids,
        active_rubric_ids=(SCOPE2_RUBRIC_ID,),
        judge_policy_id=JUDGE_POLICY_ID,
    )


def _hypothesis():
    return InterpretationHypothesis(
        hypothesis_id="hyp-scope2",
        subject_id="claim-scope2",
        claims=(
            ClaimCandidate(
                field="scope2_method",
                value="market_based",
                witness_id="span-17",
                origin="llm_inferred",
            ),
        ),
        witnesses=(
            EvidenceRef(
                witness_id="span-17",
                field="scope2_method",
                source="report.pdf",
                span="p12",
            ),
        ),
    )


def _hypothesis_with_unsupported_unit():
    return InterpretationHypothesis(
        hypothesis_id="hyp-scope2",
        subject_id="claim-scope2",
        claims=(
            ClaimCandidate(
                field="scope2_method",
                value="market_based",
                witness_id="span-17",
                origin="llm_inferred",
            ),
            ClaimCandidate(
                field="unit",
                value="mwh",
                witness_id="span-unit",
                origin="llm_inferred",
            ),
        ),
        witnesses=(
            EvidenceRef(
                witness_id="span-17",
                field="scope2_method",
                source="report.pdf",
                span="p12",
            ),
            EvidenceRef(
                witness_id="span-unit",
                field="unit",
                source="report.pdf",
                span="p13",
            ),
        ),
    )


def _hypothesis_without_source_witness():
    return InterpretationHypothesis(
        hypothesis_id="hyp-scope2",
        subject_id="claim-scope2",
        claims=(
            ClaimCandidate(
                field="scope2_method",
                value="market_based",
                witness_id=None,
                origin="llm_inferred",
            ),
        ),
        witnesses=(),
    )


def _judgment(obligation_id):
    return SemanticJudgment(
        judgment_id="judgment-scope2",
        obligation_id=obligation_id,
        verdict="supports",
        rubric_id=SCOPE2_RUBRIC_ID,
        judge="llm/model@policy-v1",
        cited_span_ids=("span-17",),
        rationale="The cited span supports the claimed Scope 2 method.",
    )


def test_tiny_domain_profile_opens_scope2_semantic_obligation():
    report = compile_with_profile(_hypothesis(), _profile())

    assert report.status == "review_required"
    assert len(report.obligations) == 1
    obligation = report.obligations[0]
    assert obligation.kind == "semantic_judgment_required"
    assert obligation.field == "scope2_method"
    assert obligation.semantic_requirement is not None
    assert obligation.semantic_requirement.rubric_id == SCOPE2_RUBRIC_ID
    assert obligation.semantic_requirement.allowed_judges == (
        "human/reviewer",
        "llm/model@policy-v1",
    )
    assert report.can_build_public_output is False


def test_profile_rule_runner_surface_matches_compat_compile_with_profile():
    report = run_profile_rules(_hypothesis(), _profile())
    compat_report = compile_with_profile(_hypothesis(), _profile())

    assert report.obligations == compat_report.obligations
    assert report.status == "review_required"


def test_compile_with_profile_merges_profile_baseline_and_rule_obligations():
    report = compile_with_profile(
        _hypothesis_with_unsupported_unit(),
        _profile(
            known_fields=("scope2_method", "unit"),
            allowed_units=("kwh",),
        ),
    )

    assert report.status == "blocked"
    assert any(
        failed.field == "unit" and failed.reason == "unsupported_unit"
        for failed in report.failed_claims
    )
    assert any(
        obligation.kind == "semantic_judgment_required"
        and obligation.field == "scope2_method"
        for obligation in report.obligations
    )


def test_profile_runner_blocks_claim_without_source_witness():
    report = compile_with_profile(_hypothesis_without_source_witness(), _profile())

    assert report.status == "blocked"
    assert report.failed_claims[0].field == "scope2_method"
    assert report.failed_claims[0].reason == "missing_source_witness"
    assert any(
        obligation.kind == "find_source_witness"
        and obligation.field == "scope2_method"
        for obligation in report.obligations
    )


def test_tiny_domain_semantic_judgment_discharges_obligation():
    report = compile_with_profile(_hypothesis(), _profile())
    obligation = report.obligations[0]

    resolved = apply_semantic_judgments(
        report,
        (_judgment(obligation.obligation_id),),
        available_span_ids=("span-17",),
    )

    assert resolved.status == "accepted"
    assert resolved.obligations == ()
    assert resolved.resolved_obligations == (obligation,)


def test_inactive_tiny_domain_rule_does_not_open_obligation():
    profile = _profile(active_rule_ids=())

    report = compile_with_profile(_hypothesis(), profile)

    assert active_rule_families(profile) == ()
    assert report.status == "accepted"
    assert report.obligations == ()
