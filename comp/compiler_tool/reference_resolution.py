from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.references import ReferenceOption
from comp.compiler_tool.report_status import with_recomputed_status

ReferenceSearchQuery = Callable[[ValidationRequirement], str | None]


def resolve_reference_search_obligations(
    report: ValidationReport,
    catalog: ReferenceCatalog,
    *,
    query_for_obligation: ReferenceSearchQuery,
    reference_type: str | None = None,
    limit: int = 10,
    retrieval_method: str = "keyword",
) -> ValidationReport:
    obligations: list[ValidationRequirement] = []
    candidates = report.reference_options
    resolved_validation_requirements = report.resolved_validation_requirements
    changed = False

    for obligation in report.validation_requirements:
        if not _is_reference_search_obligation(obligation):
            obligations.append(obligation)
            continue

        query = query_for_obligation(obligation)
        if not query:
            obligations.append(obligation)
            continue

        found = catalog.search(
            query,
            reference_type=reference_type,
            limit=limit,
            retrieval_method=retrieval_method,
        )
        if not found:
            obligations.append(obligation)
            continue

        candidates = _append_unique_candidates(candidates, found)
        resolved_validation_requirements = _append_unique_obligations(
            resolved_validation_requirements,
            (obligation,),
        )
        changed = True

    if not changed:
        return report

    return with_recomputed_status(
        replace(
            report,
            validation_requirements=tuple(obligations),
            resolved_validation_requirements=resolved_validation_requirements,
            reference_options=candidates,
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


__all__ = ["ReferenceSearchQuery", "resolve_reference_search_obligations"]
