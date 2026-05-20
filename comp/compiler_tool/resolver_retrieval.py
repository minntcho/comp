from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from string import Formatter
from typing import Any

from comp.compiler_tool.models import ProofObligation
from comp.compiler_tool.resolver_tasks import ResolverTask, resolver_task_from_obligation
from comp.compiler_tool.retrieval import ReferenceQuery, RetrievalLens


@dataclass(frozen=True)
class RetrievalQueryRule:
    rule_id: str
    lens: RetrievalLens
    text_template: str
    reference_type: str | None = None
    task_type: str = "reference_search"
    field: str | None = None
    reason: str | None = None
    formula_id: str | None = None


@dataclass(frozen=True)
class RetrievalQueryPolicy:
    policy_id: str
    rules: tuple[RetrievalQueryRule, ...] = field(default_factory=tuple)


def reference_query_from_resolver_task(
    task: ResolverTask,
    *,
    text: str,
    lens: RetrievalLens,
    reference_type: str | None = None,
) -> ReferenceQuery:
    if task.task_type != "reference_search":
        raise ValueError(
            "reference_query_from_resolver_task requires a reference_search task"
        )

    return ReferenceQuery(
        query_id=f"reference-query:{task.obligation_id}",
        text=text,
        lens=lens,
        reference_type=reference_type,
        source_artifact_ids=(task.task_id, task.obligation_id),
    )


def reference_query_for_obligation_from_policy(
    tasks: tuple[ResolverTask, ...],
    *,
    policy: RetrievalQueryPolicy,
    context: Mapping[str, Any] | None = None,
) -> Callable[[ProofObligation], ReferenceQuery | None]:
    return reference_query_for_obligation_from_policies(
        tasks,
        policies=(policy,),
        context=context,
    )


def reference_query_for_obligation_from_policies(
    tasks: tuple[ResolverTask, ...],
    *,
    policies: tuple[RetrievalQueryPolicy, ...],
    context: Mapping[str, Any] | None = None,
) -> Callable[[ProofObligation], ReferenceQuery | None]:
    context = context or {}
    queries_by_obligation_id: dict[str, ReferenceQuery] = {}
    for task in tasks:
        query = _query_for_task_from_policies(task, policies, context)
        if query is not None:
            queries_by_obligation_id[task.obligation_id] = query

    def query_for_obligation(obligation: ProofObligation) -> ReferenceQuery | None:
        obligation_id = resolver_task_from_obligation(obligation).obligation_id
        return queries_by_obligation_id.get(obligation_id)

    return query_for_obligation


def reference_query_for_obligation_from_profile_policy(
    tasks: tuple[ResolverTask, ...],
    *,
    profile,
    policy_id: str | None = None,
    context: Mapping[str, Any] | None = None,
) -> Callable[[ProofObligation], ReferenceQuery | None]:
    from comp.compiler_tool.profiles import (
        ProfileValidationError,
        active_retrieval_query_policies,
    )

    active_policies = active_retrieval_query_policies(profile)
    if policy_id is not None:
        active_policies = tuple(
            policy for policy in active_policies if policy.policy_id == policy_id
        )
        if not active_policies:
            raise ProfileValidationError(
                f"inactive retrieval policy id: {policy_id}"
            )

    return reference_query_for_obligation_from_policies(
        tasks,
        policies=active_policies,
        context=context,
    )


def reference_query_for_obligation_from_resolver_tasks(
    tasks: tuple[ResolverTask, ...],
    *,
    query_texts: Mapping[str, str],
    lens: RetrievalLens,
    reference_type: str | None = None,
) -> Callable[[ProofObligation], ReferenceQuery | None]:
    queries_by_obligation_id = {
        task.obligation_id: reference_query_from_resolver_task(
            task,
            text=query_texts[task.obligation_id],
            lens=lens,
            reference_type=reference_type,
        )
        for task in tasks
        if task.task_type == "reference_search" and task.obligation_id in query_texts
    }

    def query_for_obligation(obligation: ProofObligation) -> ReferenceQuery | None:
        obligation_id = resolver_task_from_obligation(obligation).obligation_id
        return queries_by_obligation_id.get(obligation_id)

    return query_for_obligation


def _query_for_task_from_policies(
    task: ResolverTask,
    policies: tuple[RetrievalQueryPolicy, ...],
    context: Mapping[str, Any],
) -> ReferenceQuery | None:
    for policy in policies:
        rule = _matching_rule(task, policy)
        if rule is None:
            continue

        text = _render_query_text(rule.text_template, task, context)
        if text is None:
            continue

        return reference_query_from_resolver_task(
            task,
            text=text,
            lens=rule.lens,
            reference_type=rule.reference_type,
        )
    return None


def _matching_rule(
    task: ResolverTask,
    policy: RetrievalQueryPolicy,
) -> RetrievalQueryRule | None:
    for rule in policy.rules:
        if _rule_matches_task(rule, task):
            return rule
    return None


def _rule_matches_task(rule: RetrievalQueryRule, task: ResolverTask) -> bool:
    if rule.task_type != task.task_type:
        return False
    if rule.field is not None and rule.field != task.field:
        return False
    if rule.reason is not None and rule.reason != task.reason:
        return False
    if rule.formula_id is not None and rule.formula_id != _task_value(
        task,
        "formula_id",
    ):
        return False
    return True


def _render_query_text(
    template: str,
    task: ResolverTask,
    context: Mapping[str, Any],
) -> str | None:
    values = {
        **_task_values(task),
        **context,
    }
    required_names = _template_field_names(template)
    if any(name not in values for name in required_names):
        return None
    return template.format_map(values)


def _template_field_names(template: str) -> tuple[str, ...]:
    return tuple(
        field_name
        for _, field_name, _, _ in Formatter().parse(template)
        if field_name is not None and field_name
    )


def _task_values(task: ResolverTask) -> dict[str, Any]:
    return {
        **dict(task.payload),
        "task_id": task.task_id,
        "obligation_id": task.obligation_id,
        "task_type": task.task_type,
        "obligation_kind": task.obligation_kind,
        "field": task.field,
        "reason": task.reason,
        "claim_id": task.claim_id,
    }


def _task_value(task: ResolverTask, key: str) -> Any:
    return _task_values(task).get(key)


__all__ = [
    "RetrievalQueryPolicy",
    "RetrievalQueryRule",
    "reference_query_for_obligation_from_policies",
    "reference_query_for_obligation_from_profile_policy",
    "reference_query_for_obligation_from_policy",
    "reference_query_for_obligation_from_resolver_tasks",
    "reference_query_from_resolver_task",
]
