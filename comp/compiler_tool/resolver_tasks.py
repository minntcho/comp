from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from comp.compiler_tool.calculations import CalculationRequirement
from comp.compiler_tool.models import (
    ValidationReport,
    ValidationRequirement,
    SemanticJudgmentRequirement,
)


@dataclass(frozen=True)
class ResolverTask:
    task_id: str
    requirement_id: str
    task_type: str
    required_artifact: str
    requirement_kind: str
    field: str
    reason: str
    claim_id: str | None = None
    blocking: bool = True
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)


def resolver_tasks_from_report(report: ValidationReport) -> tuple[ResolverTask, ...]:
    return tuple(
        resolver_task_from_requirement(obligation)
        for obligation in report.validation_requirements
    )


def resolver_task_from_requirement(requirement: ValidationRequirement) -> ResolverTask:
    requirement_id = _requirement_id(requirement)
    return ResolverTask(
        task_id=f"resolver-task:{requirement_id}",
        requirement_id=requirement_id,
        task_type=_task_type(requirement.kind),
        required_artifact=_required_artifact(requirement.kind),
        requirement_kind=requirement.kind,
        field=requirement.field,
        reason=requirement.reason,
        claim_id=requirement.claim_id,
        blocking=requirement.blocking,
        payload=_payload(requirement),
    )


def _task_type(requirement_kind: str) -> str:
    return {
        "semantic_judgment_required": "semantic_judgment",
        "reference_search_required": "reference_search",
        "reference_selection_required": "reference_selection",
        "reference_context_required": "reference_context",
        "find_context": "context",
        "find_source_witness": "evidence_search",
        "calculation_blocked": "calculation_resolution",
    }.get(requirement_kind, "requirement_resolution")


def _required_artifact(requirement_kind: str) -> str:
    return {
        "semantic_judgment_required": "semantic_judgment",
        "reference_search_required": "reference_options",
        "reference_selection_required": "reference_binding",
        "reference_context_required": "context_attachment",
        "find_context": "context_attachment",
        "find_source_witness": "evidence_witness",
        "calculation_blocked": "calculation_result",
    }.get(requirement_kind, "resolver_artifact")


def _payload(obligation: ValidationRequirement) -> tuple[tuple[str, Any], ...]:
    if obligation.semantic_requirement is not None:
        return _semantic_payload(obligation.semantic_requirement)
    if obligation.calculation_requirement is not None:
        return _calculation_payload(obligation.calculation_requirement)
    return ()


def _semantic_payload(
    requirement: SemanticJudgmentRequirement,
) -> tuple[tuple[str, Any], ...]:
    return (
        ("question", requirement.question),
        ("rubric_id", requirement.rubric_id),
        ("acceptable_verdicts", requirement.acceptable_verdicts),
        ("required_verdict", requirement.required_verdict),
        ("allowed_judges", requirement.allowed_judges),
        ("evidence_span_ids", requirement.evidence_span_ids),
    )


def _calculation_payload(
    requirement: CalculationRequirement,
) -> tuple[tuple[str, Any], ...]:
    items: list[tuple[str, Any]] = [
        ("calculation_reason", requirement.reason),
        ("formula_id", requirement.formula_id),
        ("output_claim_id", requirement.output_claim_id),
    ]
    items.extend(
        _present_items(
            (
                ("input_claim_id", requirement.input_claim_id),
                ("reference_binding_id", requirement.reference_binding_id),
                ("reference_id", requirement.reference_id),
                ("expected_unit", requirement.expected_unit),
                ("actual_unit", requirement.actual_unit),
                ("expected_output_unit", requirement.expected_output_unit),
                ("actual_output_unit", requirement.actual_output_unit),
                ("missing_attribute", requirement.missing_attribute),
            )
        )
    )
    return tuple(items)


def _present_items(
    items: tuple[tuple[str, Any], ...],
) -> tuple[tuple[str, Any], ...]:
    return tuple((key, value) for key, value in items if value is not None)


def _requirement_id(requirement: ValidationRequirement) -> str:
    if requirement.requirement_id is not None:
        return requirement.requirement_id
    return _stable_id(
        "validation_requirement",
        requirement.kind,
        requirement.field,
        requirement.reason,
    )


def _stable_id(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


__all__ = [
    "ResolverTask",
    "resolver_task_from_requirement",
    "resolver_tasks_from_report",
]
