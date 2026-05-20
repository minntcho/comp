import pytest

from comp.compiler_tool import (
    CompilerProfile,
    DomainPack,
    JudgePolicy,
    ProfileValidationError,
    RuleFamily,
    SemanticRubric,
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    active_rule_families,
    active_retrieval_query_policies,
    profile_declaration_fingerprint,
    profile_lock_body,
    profile_lock_envelope_body,
    validate_compiler_profile,
)


def _rule(rule_id, *, rubric_ids=()):
    return RuleFamily(
        rule_id=rule_id,
        required_rubric_ids=tuple(rubric_ids),
    )


def _rubric(rubric_id):
    return SemanticRubric(
        rubric_id=rubric_id,
        acceptable_verdicts=("supports", "refutes", "ambiguous"),
        required_verdict="supports",
    )


def _judge_policy(policy_id):
    return JudgePolicy(
        judge_policy_id=policy_id,
        allowed_judges=("human/reviewer", "llm/model@policy-v1"),
    )


def _retrieval_policy(policy_id):
    return RetrievalQueryPolicy(
        policy_id=policy_id,
        rules=(
            RetrievalQueryRule(
                rule_id=f"{policy_id}.rule",
                formula_id="fixture.formula.v1",
                lens="factor",
                reference_type="emission_factor",
                text_template="{geography} factor {reporting_year}",
            ),
        ),
    )


def _domain(
    *,
    rules,
    rubrics=(),
    judge_policies=(),
    retrieval_query_policies=(),
    disabled_core_invariants=(),
):
    return DomainPack(
        domain_id="fixture",
        version="2026.1",
        rule_families=tuple(rules),
        rubrics=tuple(rubrics),
        judge_policies=tuple(judge_policies),
        retrieval_query_policies=tuple(retrieval_query_policies),
        disabled_core_invariants=tuple(disabled_core_invariants),
    )


def test_compiler_profile_model_set_is_exported():
    assert DomainPack is not None
    assert CompilerProfile is not None
    assert RuleFamily is not None
    assert SemanticRubric is not None
    assert JudgePolicy is not None
    assert RetrievalQueryPolicy is not None
    assert RetrievalQueryRule is not None
    assert ProfileValidationError is not None
    assert active_rule_families is not None
    assert active_retrieval_query_policies is not None
    assert validate_compiler_profile is not None


def test_profile_only_activates_named_rules_in_profile_order():
    inactive = _rule("fixture.inactive_rule.v1")
    first = _rule("fixture.first_rule.v1")
    second = _rule("fixture.second_rule.v1")
    domain = _domain(rules=(inactive, first, second))
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(domain,),
        active_rule_ids=("fixture.second_rule.v1", "fixture.first_rule.v1"),
    )

    validate_compiler_profile(profile)

    assert active_rule_families(profile) == (second, first)


def test_profile_validation_rejects_unknown_active_rule_id():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(_domain(rules=(_rule("fixture.known_rule.v1"),)),),
        active_rule_ids=("fixture.missing_rule.v1",),
    )

    with pytest.raises(ProfileValidationError, match="unknown active rule"):
        validate_compiler_profile(profile)


def test_profile_validation_rejects_unknown_active_rubric_id():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(_domain(rules=(), rubrics=(_rubric("fixture.rubric.v1"),)),),
        active_rubric_ids=("fixture.missing_rubric.v1",),
    )

    with pytest.raises(ProfileValidationError, match="unknown active rubric"):
        validate_compiler_profile(profile)


def test_profile_validation_rejects_unknown_judge_policy_id():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(rules=(), judge_policies=(_judge_policy("fixture.judge_policy.v1"),)),
        ),
        judge_policy_id="fixture.missing_judge_policy.v1",
    )

    with pytest.raises(ProfileValidationError, match="unknown judge policy"):
        validate_compiler_profile(profile)


def test_profile_only_activates_named_retrieval_policies_in_profile_order():
    inactive = _retrieval_policy("fixture.inactive_retrieval_policy.v1")
    first = _retrieval_policy("fixture.first_retrieval_policy.v1")
    second = _retrieval_policy("fixture.second_retrieval_policy.v1")
    domain = _domain(
        rules=(),
        retrieval_query_policies=(inactive, first, second),
    )
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(domain,),
        active_retrieval_policy_ids=(
            "fixture.second_retrieval_policy.v1",
            "fixture.first_retrieval_policy.v1",
        ),
    )

    validate_compiler_profile(profile)

    assert active_retrieval_query_policies(profile) == (second, first)


def test_profile_validation_rejects_unknown_active_retrieval_policy_id():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(),
                retrieval_query_policies=(
                    _retrieval_policy("fixture.known_retrieval_policy.v1"),
                ),
            ),
        ),
        active_retrieval_policy_ids=("fixture.missing_retrieval_policy.v1",),
    )

    with pytest.raises(ProfileValidationError, match="unknown active retrieval policy"):
        validate_compiler_profile(profile)


def test_rule_required_rubrics_must_be_active_in_profile():
    rule = _rule(
        "fixture.semantic_rule.v1",
        rubric_ids=("fixture.semantic_rubric.v1",),
    )
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(rule,),
                rubrics=(_rubric("fixture.semantic_rubric.v1"),),
            ),
        ),
        active_rule_ids=("fixture.semantic_rule.v1",),
        active_rubric_ids=(),
    )

    with pytest.raises(ProfileValidationError, match="inactive required rubric"):
        validate_compiler_profile(profile)


def test_domain_pack_cannot_disable_core_invariants():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(),
                disabled_core_invariants=("receipt_required_for_projection",),
            ),
        ),
    )

    with pytest.raises(ProfileValidationError, match="cannot disable core invariant"):
        validate_compiler_profile(profile)


def test_duplicate_rule_ids_are_rejected():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(
                    _rule("fixture.duplicate.v1"),
                    _rule("fixture.duplicate.v1"),
                ),
            ),
        ),
    )

    with pytest.raises(ProfileValidationError, match="duplicate rule id"):
        validate_compiler_profile(profile)


def test_duplicate_retrieval_policy_ids_are_rejected():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(),
                retrieval_query_policies=(
                    _retrieval_policy("fixture.duplicate_retrieval_policy.v1"),
                    _retrieval_policy("fixture.duplicate_retrieval_policy.v1"),
                ),
            ),
        ),
    )

    with pytest.raises(ProfileValidationError, match="duplicate retrieval policy id"):
        validate_compiler_profile(profile)


def test_profile_declaration_fingerprint_pins_active_behavior_ids():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(_rule("fixture.rule.v1"),),
                rubrics=(_rubric("fixture.rubric.v1"),),
                judge_policies=(_judge_policy("fixture.judge_policy.v1"),),
                retrieval_query_policies=(
                    _retrieval_policy("fixture.retrieval_policy.v1"),
                ),
            ),
        ),
        active_rule_ids=("fixture.rule.v1",),
        active_rubric_ids=("fixture.rubric.v1",),
        active_retrieval_policy_ids=("fixture.retrieval_policy.v1",),
        judge_policy_id="fixture.judge_policy.v1",
        projection_policy_id="fixture.projection.v1",
    )

    fingerprint = profile_declaration_fingerprint(profile)
    same_fingerprint = profile_declaration_fingerprint(profile)
    changed_fingerprint = profile_declaration_fingerprint(
        CompilerProfile(
            profile_id="fixture-profile",
            domain_packs=profile.domain_packs,
            active_rule_ids=(),
            active_rubric_ids=("fixture.rubric.v1",),
            active_retrieval_policy_ids=("fixture.retrieval_policy.v1",),
            judge_policy_id="fixture.judge_policy.v1",
            projection_policy_id="fixture.projection.v1",
        )
    )

    assert fingerprint.dependency_kind == "compiler_profile"
    assert fingerprint.dependency_id == "fixture-profile"
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == same_fingerprint
    assert fingerprint != changed_fingerprint


def test_profile_lock_body_exposes_active_behavior_manifest():
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            _domain(
                rules=(_rule("fixture.rule.v1"),),
                rubrics=(_rubric("fixture.rubric.v1"),),
                judge_policies=(_judge_policy("fixture.judge_policy.v1"),),
                retrieval_query_policies=(
                    _retrieval_policy("fixture.retrieval_policy.v1"),
                ),
            ),
        ),
        active_rule_ids=("fixture.rule.v1",),
        active_rubric_ids=("fixture.rubric.v1",),
        active_retrieval_policy_ids=("fixture.retrieval_policy.v1",),
        judge_policy_id="fixture.judge_policy.v1",
        projection_policy_id="fixture.projection.v1",
    )

    body = profile_lock_body(profile)
    envelope_body = profile_lock_envelope_body(profile)

    assert body["profile_id"] == "fixture-profile"
    assert body["active_rule_ids"] == ("fixture.rule.v1",)
    assert body["active_rubric_ids"] == ("fixture.rubric.v1",)
    assert body["active_retrieval_policy_ids"] == (
        "fixture.retrieval_policy.v1",
    )
    assert body["judge_policy_id"] == "fixture.judge_policy.v1"
    assert body["projection_policy_id"] == "fixture.projection.v1"
    assert body["domain_packs"][0]["domain_id"] == "fixture"
    assert envelope_body["dependency_kind"] == "compiler_profile"
    assert envelope_body["dependency_id"] == "fixture-profile"
    assert envelope_body["profile_lock"] == body
    assert (
        envelope_body["fingerprint"]
        == profile_declaration_fingerprint(profile).fingerprint
    )
