import pytest

from comp.compiler_tool import (
    CompilerProfile,
    DomainPack,
    JudgePolicy,
    ProfileValidationError,
    RuleFamily,
    SemanticRubric,
    active_rule_families,
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


def _domain(
    *,
    rules,
    rubrics=(),
    judge_policies=(),
    disabled_core_invariants=(),
):
    return DomainPack(
        domain_id="fixture",
        version="2026.1",
        rule_families=tuple(rules),
        rubrics=tuple(rubrics),
        judge_policies=tuple(judge_policies),
        disabled_core_invariants=tuple(disabled_core_invariants),
    )


def test_compiler_profile_model_set_is_exported():
    assert DomainPack is not None
    assert CompilerProfile is not None
    assert RuleFamily is not None
    assert SemanticRubric is not None
    assert JudgePolicy is not None
    assert ProfileValidationError is not None
    assert active_rule_families is not None
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
