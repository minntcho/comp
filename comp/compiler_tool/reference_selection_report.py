from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.models import CompileReport, ProofObligation
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.reference_selector import (
    ReferenceSelectionCriteria,
    select_reference_binding,
)
from comp.compiler_tool.references import ReferenceBinding
from comp.compiler_tool.report_status import with_recomputed_status


def apply_reference_selection(
    report: CompileReport,
    catalog: ReferenceCatalog,
    *,
    criteria: ReferenceSelectionCriteria,
    field: str,
) -> CompileReport:
    result = select_reference_binding(
        candidates=report.reference_candidates,
        catalog=catalog,
        criteria=criteria,
    )
    obligation_id = _selection_obligation_id(criteria)

    if result.status == "bound" and result.binding is not None:
        open_obligations = tuple(
            obligation
            for obligation in report.obligations
            if not _matches_selection_obligation(obligation, obligation_id)
        )
        resolved = tuple(
            obligation
            for obligation in report.obligations
            if _matches_selection_obligation(obligation, obligation_id)
        )
        return with_recomputed_status(
            replace(
                report,
                obligations=open_obligations,
                resolved_obligations=_append_unique_obligations(
                    report.resolved_obligations,
                    resolved,
                ),
                reference_bindings=_append_unique_bindings(
                    report.reference_bindings,
                    (result.binding,),
                ),
                can_project_public_row=False,
            )
        )

    obligation = ProofObligation(
        kind="reference_selection_required",
        field=field,
        reason=result.status,
        obligation_id=obligation_id,
        claim_id=criteria.claim_id,
        blocking=True,
    )
    return with_recomputed_status(
        replace(
            report,
            obligations=_append_unique_obligation_by_id(report.obligations, obligation),
            can_project_public_row=False,
        )
    )


def _selection_obligation_id(criteria: ReferenceSelectionCriteria) -> str:
    return f"reference_selection:{criteria.selector_rule_id}:{criteria.claim_id}"


def _matches_selection_obligation(
    obligation: ProofObligation,
    obligation_id: str,
) -> bool:
    return (
        obligation.kind == "reference_selection_required"
        and obligation.obligation_id == obligation_id
    )


def _append_unique_bindings(
    existing: tuple[ReferenceBinding, ...],
    additions: tuple[ReferenceBinding, ...],
) -> tuple[ReferenceBinding, ...]:
    result = existing
    for binding in additions:
        if binding not in result:
            result = (*result, binding)
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


def _append_unique_obligation_by_id(
    existing: tuple[ProofObligation, ...],
    addition: ProofObligation,
) -> tuple[ProofObligation, ...]:
    if addition.obligation_id is not None and any(
        obligation.obligation_id == addition.obligation_id
        for obligation in existing
    ):
        return existing
    if addition in existing:
        return existing
    return (*existing, addition)


__all__ = ["apply_reference_selection"]
