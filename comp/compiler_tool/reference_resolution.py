from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from comp.compiler_tool.models import CompileReport, ProofObligation
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.references import ReferenceCandidate

ReferenceSearchQuery = Callable[[ProofObligation], str | None]


def resolve_reference_search_obligations(
    report: CompileReport,
    catalog: ReferenceCatalog,
    *,
    query_for_obligation: ReferenceSearchQuery,
    reference_type: str | None = None,
    limit: int = 10,
    retrieval_method: str = "keyword",
) -> CompileReport:
    obligations: list[ProofObligation] = []
    candidates = report.reference_candidates
    resolved_obligations = report.resolved_obligations
    changed = False

    for obligation in report.obligations:
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
        resolved_obligations = _append_unique_obligations(
            resolved_obligations,
            (obligation,),
        )
        changed = True

    if not changed:
        return report

    return replace(
        report,
        obligations=tuple(obligations),
        resolved_obligations=resolved_obligations,
        reference_candidates=candidates,
        can_project_public_row=False,
    )


def _is_reference_search_obligation(obligation: ProofObligation) -> bool:
    return (
        obligation.kind == "reference_search_required"
        and obligation.calculation_requirement is not None
    )


def _append_unique_candidates(
    existing: tuple[ReferenceCandidate, ...],
    additions: tuple[ReferenceCandidate, ...],
) -> tuple[ReferenceCandidate, ...]:
    result = existing
    for candidate in additions:
        if candidate not in result:
            result = (*result, candidate)
    return result


def _append_unique_obligations(
    existing: tuple[ProofObligation, ...],
    additions: tuple[ProofObligation, ...],
) -> tuple[ProofObligation, ...]:
    result = existing
    for obligation in additions:
        if obligation not in result:
            result = (*result, obligation)
    return result


__all__ = ["ReferenceSearchQuery", "resolve_reference_search_obligations"]
