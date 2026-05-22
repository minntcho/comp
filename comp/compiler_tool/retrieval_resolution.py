from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.compiler_tool.references import ReferenceOption
from comp.compiler_tool.report_status import with_recomputed_status
from comp.compiler_tool.retrieval import ReferenceQuery, ReferenceResolver

ReferenceRetrievalQuery = Callable[[ValidationRequirement], ReferenceQuery | None]


def resolve_reference_retrieval_obligations(
    report: ValidationReport,
    resolver: ReferenceResolver,
    *,
    query_for_obligation: ReferenceRetrievalQuery,
    limit: int = 10,
) -> ValidationReport:
    obligations: list[ValidationRequirement] = []
    candidates = report.reference_candidates
    resolved_obligations = report.resolved_obligations
    changed = False

    for obligation in report.obligations:
        if not _is_reference_search_obligation(obligation):
            obligations.append(obligation)
            continue

        query = query_for_obligation(obligation)
        if query is None:
            obligations.append(obligation)
            continue

        found = resolver.search(query, limit=limit)
        if not found:
            obligations.append(obligation)
            continue

        candidates = _append_unique_candidates(candidates, found)
        resolved_obligations = _append_unique_obligations(
            resolved_obligations,
            (obligation,),
        )
        changed = True

    if not changed:
        return report

    return with_recomputed_status(
        replace(
            report,
            obligations=tuple(obligations),
            resolved_obligations=resolved_obligations,
            reference_candidates=candidates,
            can_build_public_output=False,
        )
    )


def _is_reference_search_obligation(obligation: ValidationRequirement) -> bool:
    return (
        obligation.kind == "reference_search_required"
        and obligation.calculation_requirement is not None
    )


def _append_unique_candidates(
    existing: tuple[ReferenceOption, ...],
    additions: tuple[ReferenceOption, ...],
) -> tuple[ReferenceOption, ...]:
    result = existing
    for candidate in additions:
        if candidate not in result:
            result = (*result, candidate)
    return result


def _append_unique_obligations(
    existing: tuple[ValidationRequirement, ...],
    additions: tuple[ValidationRequirement, ...],
) -> tuple[ValidationRequirement, ...]:
    result = existing
    for obligation in additions:
        if obligation not in result:
            result = (*result, obligation)
    return result


__all__ = [
    "ReferenceRetrievalQuery",
    "resolve_reference_retrieval_obligations",
]
