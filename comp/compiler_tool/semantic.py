from __future__ import annotations

from collections.abc import Iterable

from comp.compiler_tool.models import (
    CompileReport,
    Hazard,
    ProofObligation,
    SemanticJudgment,
)


def apply_semantic_judgments(
    report: CompileReport,
    judgments: Iterable[SemanticJudgment],
    *,
    available_span_ids: Iterable[str] | None = None,
) -> CompileReport:
    """Discharge semantic obligations when submitted judgments satisfy protocol."""

    judgments_by_obligation: dict[str, list[SemanticJudgment]] = {}
    for judgment in judgments:
        judgments_by_obligation.setdefault(judgment.obligation_id, []).append(judgment)

    available_spans = (
        frozenset(available_span_ids) if available_span_ids is not None else None
    )
    open_obligations: list[ProofObligation] = []
    newly_resolved: list[ProofObligation] = []
    hazards = list(report.hazards)

    for obligation in report.obligations:
        if obligation.kind != "semantic_judgment_required":
            open_obligations.append(obligation)
            continue

        matching = judgments_by_obligation.get(_obligation_id(obligation), [])
        valid = [
            judgment
            for judgment in matching
            if _judgment_satisfies_protocol(
                obligation,
                judgment,
                available_span_ids=available_spans,
            )
        ]

        verdicts = {judgment.verdict for judgment in valid}
        if len(verdicts) > 1:
            open_obligations.append(obligation)
            _add_hazard(
                hazards,
                Hazard(
                    kind="conflicting_semantic_judgment",
                    field=obligation.field,
                    severity="review",
                ),
            )
            continue

        required_verdict = obligation.semantic_requirement.required_verdict if (
            obligation.semantic_requirement is not None
        ) else "supports"
        if valid and valid[0].verdict == required_verdict:
            newly_resolved.append(obligation)
            continue

        open_obligations.append(obligation)

    return CompileReport(
        status=_status_for(
            report=report,
            open_obligations=tuple(open_obligations),
            hazards=tuple(hazards),
        ),
        checked_claims=report.checked_claims,
        failed_claims=report.failed_claims,
        unknowns=report.unknowns,
        unchecked_areas=report.unchecked_areas,
        obligations=tuple(open_obligations),
        resolved_obligations=(
            *report.resolved_obligations,
            *tuple(newly_resolved),
        ),
        hazards=tuple(hazards),
        reference_candidates=report.reference_candidates,
        reference_bindings=report.reference_bindings,
        can_project_public_row=report.can_project_public_row,
    )


def _judgment_satisfies_protocol(
    obligation: ProofObligation,
    judgment: SemanticJudgment,
    *,
    available_span_ids: frozenset[str] | None,
) -> bool:
    requirement = obligation.semantic_requirement
    if requirement is None:
        return False

    if judgment.rubric_id != requirement.rubric_id:
        return False

    if judgment.verdict not in requirement.acceptable_verdicts:
        return False

    if requirement.allowed_judges and judgment.judge not in requirement.allowed_judges:
        return False

    cited_span_ids = set(judgment.cited_span_ids)
    if not set(requirement.evidence_span_ids).issubset(cited_span_ids):
        return False

    if available_span_ids is not None and not cited_span_ids.issubset(available_span_ids):
        return False

    return True


def _status_for(
    *,
    report: CompileReport,
    open_obligations: tuple[ProofObligation, ...],
    hazards: tuple[Hazard, ...],
) -> str:
    if report.failed_claims:
        return "blocked"
    if hazards:
        return "review_required"
    if any(
        obligation.kind == "semantic_judgment_required" and obligation.blocking
        for obligation in open_obligations
    ):
        return "review_required"
    if report.unchecked_areas:
        return "unchecked"
    if report.unknowns:
        return "underconstrained"
    return "accepted"


def _obligation_id(obligation: ProofObligation) -> str:
    if obligation.obligation_id:
        return obligation.obligation_id
    return f"{obligation.kind}:{obligation.field}:{obligation.reason}"


def _add_hazard(hazards: list[Hazard], hazard: Hazard) -> None:
    if hazard not in hazards:
        hazards.append(hazard)


__all__ = ["apply_semantic_judgments"]
