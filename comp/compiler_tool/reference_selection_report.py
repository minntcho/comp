from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.reference_selector import (
    ReferenceSelectionCriteria,
    select_reference_binding,
)
from comp.compiler_tool.references import CanonicalReference
from comp.compiler_tool.report_status import with_recomputed_status


def apply_reference_selection(
    report: ValidationReport,
    catalog: ReferenceCatalog,
    *,
    criteria: ReferenceSelectionCriteria,
    field: str,
) -> ValidationReport:
    result = select_reference_binding(
        candidates=report.reference_options,
        catalog=catalog,
        criteria=criteria,
    )
    requirement_id = _selection_requirement_id(criteria)

    if result.status == "bound" and result.binding is not None:
        open_obligations = tuple(
            obligation
            for obligation in report.validation_requirements
            if not _matches_selection_requirement(obligation, requirement_id)
        )
        resolved = tuple(
            obligation
            for obligation in report.validation_requirements
            if _matches_selection_requirement(obligation, requirement_id)
        )
        return with_recomputed_status(
            replace(
                report,
                validation_requirements=open_obligations,
                resolved_validation_requirements=_append_unique_obligations(
                    report.resolved_validation_requirements,
                    resolved,
                ),
                canonical_references=_append_unique_bindings(
                    report.canonical_references,
                    (result.binding,),
                ),
                can_build_public_output=False,
            )
        )

    obligation = ValidationRequirement(
        kind="reference_selection_required",
        field=field,
        reason=result.status,
        requirement_id=requirement_id,
        claim_id=criteria.claim_id,
        blocking=True,
    )
    return with_recomputed_status(
        replace(
            report,
            validation_requirements=_append_unique_obligation_by_id(report.validation_requirements, obligation),
            can_build_public_output=False,
        )
    )


def _selection_requirement_id(criteria: ReferenceSelectionCriteria) -> str:
    return f"reference_selection:{criteria.selector_rule_id}:{criteria.claim_id}"


def _matches_selection_requirement(
    requirement: ValidationRequirement,
    requirement_id: str,
) -> bool:
    return (
        requirement.kind == "reference_selection_required"
        and requirement.requirement_id == requirement_id
    )


def _append_unique_bindings(
    existing: tuple[CanonicalReference, ...],
    additions: tuple[CanonicalReference, ...],
) -> tuple[CanonicalReference, ...]:
    result = existing
    for binding in additions:
        if binding not in result:
            result = (*result, binding)
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


def _append_unique_obligation_by_id(
    existing: tuple[ValidationRequirement, ...],
    addition: ValidationRequirement,
) -> tuple[ValidationRequirement, ...]:
    if addition.requirement_id is not None and any(
        requirement.requirement_id == addition.requirement_id
        for requirement in existing
    ):
        return existing
    if addition in existing:
        return existing
    return (*existing, addition)


__all__ = ["apply_reference_selection"]
