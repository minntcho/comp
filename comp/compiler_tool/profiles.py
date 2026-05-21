from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from comp.judgment.receipts import DependencyFingerprint

if TYPE_CHECKING:
    from comp.compiler_tool.resolver_retrieval import RetrievalQueryPolicy

RuleEvaluator = Callable[[Any, Any, "CompilerProfile"], tuple[Any, ...]]


class ProfileValidationError(ValueError):
    """Raised when a compiler profile cannot lock a coherent behavior set."""


@dataclass(frozen=True)
class RuleFamily:
    rule_id: str
    required_rubric_ids: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    evaluate: RuleEvaluator | None = None
    evaluator_id: str | None = None
    implementation_version: str | None = None


@dataclass(frozen=True)
class SemanticRubric:
    rubric_id: str
    acceptable_verdicts: tuple[str, ...]
    required_verdict: str = "supports"
    description: str = ""

    def requirement(
        self,
        *,
        question: str,
        claim_id: str,
        evidence_span_ids: tuple[str, ...] = (),
        allowed_judges: tuple[str, ...] = (),
    ):
        from comp.compiler_tool.models import SemanticJudgmentRequirement

        return SemanticJudgmentRequirement(
            question=question,
            claim_id=claim_id,
            evidence_span_ids=evidence_span_ids,
            rubric_id=self.rubric_id,
            acceptable_verdicts=self.acceptable_verdicts,
            required_verdict=self.required_verdict,
            allowed_judges=allowed_judges,
        )


@dataclass(frozen=True)
class JudgePolicy:
    judge_policy_id: str
    allowed_judges: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass(frozen=True)
class DomainPack:
    domain_id: str
    version: str
    known_fields: tuple[str, ...] = field(default_factory=tuple)
    allowed_units: tuple[str, ...] = field(default_factory=tuple)
    rule_families: tuple[RuleFamily, ...] = field(default_factory=tuple)
    rubrics: tuple[SemanticRubric, ...] = field(default_factory=tuple)
    judge_policies: tuple[JudgePolicy, ...] = field(default_factory=tuple)
    retrieval_query_policies: tuple["RetrievalQueryPolicy", ...] = field(
        default_factory=tuple
    )
    disabled_core_invariants: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CompilerProfile:
    profile_id: str
    domain_packs: tuple[DomainPack, ...] = field(default_factory=tuple)
    active_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    active_rubric_ids: tuple[str, ...] = field(default_factory=tuple)
    active_retrieval_policy_ids: tuple[str, ...] = field(default_factory=tuple)
    judge_policy_id: str | None = None
    projection_policy_id: str | None = None
    core_invariant_version: str = "core-invariants-v1"

    def rubric(self, rubric_id: str) -> SemanticRubric:
        _, rubrics, _, _ = _catalogs(self)
        try:
            return rubrics[rubric_id]
        except KeyError as exc:
            raise ProfileValidationError(f"unknown rubric id: {rubric_id}") from exc

    def judge_policy(self) -> JudgePolicy:
        if self.judge_policy_id is None:
            return JudgePolicy(judge_policy_id="default-empty-judge-policy")
        _, _, judge_policies, _ = _catalogs(self)
        try:
            return judge_policies[self.judge_policy_id]
        except KeyError as exc:
            raise ProfileValidationError(
                f"unknown judge policy id: {self.judge_policy_id}"
            ) from exc


def validate_compiler_profile(profile: CompilerProfile) -> None:
    rules, rubrics, judge_policies, retrieval_policies = _catalogs(profile)

    for domain in profile.domain_packs:
        if domain.disabled_core_invariants:
            disabled = ", ".join(domain.disabled_core_invariants)
            raise ProfileValidationError(
                f"domain pack {domain.domain_id!r} cannot disable core invariant(s): {disabled}"
            )

    for rule_id in profile.active_rule_ids:
        if rule_id not in rules:
            raise ProfileValidationError(f"unknown active rule id: {rule_id}")

    for rubric_id in profile.active_rubric_ids:
        if rubric_id not in rubrics:
            raise ProfileValidationError(f"unknown active rubric id: {rubric_id}")

    for policy_id in profile.active_retrieval_policy_ids:
        if policy_id not in retrieval_policies:
            raise ProfileValidationError(
                f"unknown active retrieval policy id: {policy_id}"
            )

    if profile.judge_policy_id is not None and profile.judge_policy_id not in judge_policies:
        raise ProfileValidationError(f"unknown judge policy id: {profile.judge_policy_id}")

    active_rubrics = set(profile.active_rubric_ids)
    for rule in active_rule_families(profile, validate=False):
        if rule.evaluate is not None and (
            not rule.evaluator_id or not rule.implementation_version
        ):
            raise ProfileValidationError(
                f"active rule {rule.rule_id} requires evaluator identity and "
                "implementation version"
            )
        for rubric_id in rule.required_rubric_ids:
            if rubric_id not in rubrics:
                raise ProfileValidationError(
                    f"unknown required rubric id {rubric_id} for rule {rule.rule_id}"
                )
            if rubric_id not in active_rubrics:
                raise ProfileValidationError(
                    f"inactive required rubric id {rubric_id} for rule {rule.rule_id}"
                )


def active_rule_families(
    profile: CompilerProfile,
    *,
    validate: bool = True,
) -> tuple[RuleFamily, ...]:
    if validate:
        validate_compiler_profile(profile)
    rules, _, _, _ = _catalogs(profile)
    return tuple(rules[rule_id] for rule_id in profile.active_rule_ids)


def active_retrieval_query_policies(
    profile: CompilerProfile,
    *,
    validate: bool = True,
) -> tuple["RetrievalQueryPolicy", ...]:
    if validate:
        validate_compiler_profile(profile)
    _, _, _, retrieval_policies = _catalogs(profile)
    return tuple(
        retrieval_policies[policy_id]
        for policy_id in profile.active_retrieval_policy_ids
    )


def profile_known_fields(
    profile: CompilerProfile,
    *,
    validate: bool = True,
) -> frozenset[str]:
    if validate:
        validate_compiler_profile(profile)
    return frozenset(
        field
        for domain in profile.domain_packs
        for field in domain.known_fields
    )


def profile_allowed_units(
    profile: CompilerProfile,
    *,
    validate: bool = True,
) -> frozenset[str]:
    if validate:
        validate_compiler_profile(profile)
    return frozenset(
        unit.lower()
        for domain in profile.domain_packs
        for unit in domain.allowed_units
    )


def profile_declaration_fingerprint(
    profile: CompilerProfile,
) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="compiler_profile",
        dependency_id=profile.profile_id,
        payload=profile_lock_body(profile),
    )


def profile_lock_body(profile: CompilerProfile) -> dict[str, Any]:
    validate_compiler_profile(profile)
    return {
        "profile_id": profile.profile_id,
        "core_invariant_version": profile.core_invariant_version,
        "active_rule_ids": profile.active_rule_ids,
        "active_rubric_ids": profile.active_rubric_ids,
        "active_retrieval_policy_ids": profile.active_retrieval_policy_ids,
        "judge_policy_id": profile.judge_policy_id,
        "projection_policy_id": profile.projection_policy_id,
        "domain_packs": tuple(
            _domain_pack_fingerprint_payload(domain)
            for domain in profile.domain_packs
        ),
    }


def profile_lock_envelope_body(profile: CompilerProfile) -> dict[str, Any]:
    fingerprint = profile_declaration_fingerprint(profile)
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
        "profile_lock": profile_lock_body(profile),
    }


def domain_pack_declaration_fingerprint(domain: DomainPack) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="domain_pack",
        dependency_id=f"domain_pack:{domain.domain_id}:{domain.version}",
        payload=_domain_pack_fingerprint_payload(domain),
    )


def rule_family_declaration_fingerprint(rule: RuleFamily) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="rule_family",
        dependency_id=rule.rule_id,
        payload=_rule_family_fingerprint_payload(rule),
    )


def semantic_rubric_declaration_fingerprint(
    rubric: SemanticRubric,
) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="semantic_rubric",
        dependency_id=rubric.rubric_id,
        payload=_semantic_rubric_fingerprint_payload(rubric),
    )


def _catalogs(
    profile: CompilerProfile,
) -> tuple[
    dict[str, RuleFamily],
    dict[str, SemanticRubric],
    dict[str, JudgePolicy],
    dict[str, "RetrievalQueryPolicy"],
]:
    return (
        _unique_by_id(
            [
                rule
                for domain in profile.domain_packs
                for rule in domain.rule_families
            ],
            attr="rule_id",
            label="rule id",
        ),
        _unique_by_id(
            [
                rubric
                for domain in profile.domain_packs
                for rubric in domain.rubrics
            ],
            attr="rubric_id",
            label="rubric id",
        ),
        _unique_by_id(
            [
                policy
                for domain in profile.domain_packs
                for policy in domain.judge_policies
            ],
            attr="judge_policy_id",
            label="judge policy id",
        ),
        _unique_by_id(
            [
                policy
                for domain in profile.domain_packs
                for policy in domain.retrieval_query_policies
            ],
            attr="policy_id",
            label="retrieval policy id",
        ),
    )


T = TypeVar("T")


def _unique_by_id(items: list[T], *, attr: str, label: str) -> dict[str, T]:
    out: dict[str, T] = {}
    for item in items:
        item_id = getattr(item, attr)
        if item_id in out:
            raise ProfileValidationError(f"duplicate {label}: {item_id}")
        out[item_id] = item
    return out


def _domain_pack_fingerprint_payload(domain: DomainPack) -> dict[str, Any]:
    return {
        "domain_id": domain.domain_id,
        "version": domain.version,
        "known_fields": domain.known_fields,
        "allowed_units": domain.allowed_units,
        "rule_families": tuple(
            _rule_family_fingerprint_payload(rule)
            for rule in domain.rule_families
        ),
        "rubrics": tuple(
            _semantic_rubric_fingerprint_payload(rubric)
            for rubric in domain.rubrics
        ),
        "judge_policies": tuple(
            _judge_policy_fingerprint_payload(policy)
            for policy in domain.judge_policies
        ),
        "retrieval_query_policies": tuple(
            _retrieval_query_policy_fingerprint_payload(policy)
            for policy in domain.retrieval_query_policies
        ),
        "disabled_core_invariants": domain.disabled_core_invariants,
    }


def _rule_family_fingerprint_payload(rule: RuleFamily) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "required_rubric_ids": rule.required_rubric_ids,
        "description": rule.description,
        "evaluator_id": rule.evaluator_id,
        "implementation_version": rule.implementation_version,
    }


def _semantic_rubric_fingerprint_payload(rubric: SemanticRubric) -> dict[str, Any]:
    return {
        "rubric_id": rubric.rubric_id,
        "acceptable_verdicts": rubric.acceptable_verdicts,
        "required_verdict": rubric.required_verdict,
        "description": rubric.description,
    }


def _judge_policy_fingerprint_payload(policy: JudgePolicy) -> dict[str, Any]:
    return {
        "judge_policy_id": policy.judge_policy_id,
        "allowed_judges": policy.allowed_judges,
        "description": policy.description,
    }


def _retrieval_query_policy_fingerprint_payload(policy) -> dict[str, Any]:
    return {
        "policy_id": policy.policy_id,
        "rules": tuple(
            {
                "rule_id": rule.rule_id,
                "lens": rule.lens,
                "text_template": rule.text_template,
                "reference_type": rule.reference_type,
                "task_type": rule.task_type,
                "field": rule.field,
                "reason": rule.reason,
                "formula_id": rule.formula_id,
            }
            for rule in policy.rules
        ),
    }


__all__ = [
    "RuleFamily",
    "SemanticRubric",
    "JudgePolicy",
    "DomainPack",
    "CompilerProfile",
    "ProfileValidationError",
    "validate_compiler_profile",
    "active_rule_families",
    "active_retrieval_query_policies",
    "profile_known_fields",
    "profile_allowed_units",
    "profile_declaration_fingerprint",
    "profile_lock_body",
    "profile_lock_envelope_body",
    "domain_pack_declaration_fingerprint",
    "rule_family_declaration_fingerprint",
    "semantic_rubric_declaration_fingerprint",
]
