from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar


class ProfileValidationError(ValueError):
    """Raised when a compiler profile cannot lock a coherent behavior set."""


@dataclass(frozen=True)
class RuleFamily:
    rule_id: str
    required_rubric_ids: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass(frozen=True)
class SemanticRubric:
    rubric_id: str
    acceptable_verdicts: tuple[str, ...]
    required_verdict: str = "supports"
    description: str = ""


@dataclass(frozen=True)
class JudgePolicy:
    judge_policy_id: str
    allowed_judges: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass(frozen=True)
class DomainPack:
    domain_id: str
    version: str
    rule_families: tuple[RuleFamily, ...] = field(default_factory=tuple)
    rubrics: tuple[SemanticRubric, ...] = field(default_factory=tuple)
    judge_policies: tuple[JudgePolicy, ...] = field(default_factory=tuple)
    disabled_core_invariants: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CompilerProfile:
    profile_id: str
    domain_packs: tuple[DomainPack, ...] = field(default_factory=tuple)
    active_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    active_rubric_ids: tuple[str, ...] = field(default_factory=tuple)
    judge_policy_id: str | None = None
    projection_policy_id: str | None = None
    core_invariant_version: str = "core-invariants-v1"


def validate_compiler_profile(profile: CompilerProfile) -> None:
    rules, rubrics, judge_policies = _catalogs(profile)

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

    if profile.judge_policy_id is not None and profile.judge_policy_id not in judge_policies:
        raise ProfileValidationError(f"unknown judge policy id: {profile.judge_policy_id}")

    active_rubrics = set(profile.active_rubric_ids)
    for rule in active_rule_families(profile, validate=False):
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
    rules, _, _ = _catalogs(profile)
    return tuple(rules[rule_id] for rule_id in profile.active_rule_ids)


def _catalogs(
    profile: CompilerProfile,
) -> tuple[dict[str, RuleFamily], dict[str, SemanticRubric], dict[str, JudgePolicy]]:
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


__all__ = [
    "RuleFamily",
    "SemanticRubric",
    "JudgePolicy",
    "DomainPack",
    "CompilerProfile",
    "ProfileValidationError",
    "validate_compiler_profile",
    "active_rule_families",
]
