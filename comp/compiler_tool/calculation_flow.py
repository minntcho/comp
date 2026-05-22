from __future__ import annotations

from comp.compiler_tool.calculation_resolution import plan_calculation_resolution
from comp.compiler_tool.calculation_retry import retry_blocked_calculation
from comp.compiler_tool.calculations import CalculationFormula, CalculationInput
from comp.compiler_tool.models import ValidationReport
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.reference_resolution import (
    ReferenceSearchQuery,
    resolve_reference_search_obligations,
)
from comp.compiler_tool.reference_selection_report import apply_reference_selection
from comp.compiler_tool.reference_selector import ReferenceSelectionCriteria
from comp.compiler_tool.references import CanonicalReference


def resolve_reference_grounded_calculation(
    report: ValidationReport,
    catalog: ReferenceCatalog,
    *,
    query_for_obligation: ReferenceSearchQuery,
    criteria: ReferenceSelectionCriteria,
    input_claim: CalculationInput,
    formula: CalculationFormula,
    output_claim_id: str,
    limit: int = 10,
    retrieval_method: str = "keyword",
) -> ValidationReport:
    planned = plan_calculation_resolution(report)
    if not _has_reference_search_obligation(planned):
        return planned

    searched = resolve_reference_search_obligations(
        planned,
        catalog,
        query_for_obligation=query_for_obligation,
        reference_type=criteria.reference_type,
        limit=limit,
        retrieval_method=retrieval_method,
    )
    if _has_reference_search_obligation(searched):
        return searched

    selected = apply_reference_selection(
        searched,
        catalog,
        criteria=criteria,
        field=formula.output_field,
    )
    binding = _binding_for(selected.canonical_references, criteria.binding_id)
    if binding is None:
        return selected

    return retry_blocked_calculation(
        selected,
        catalog,
        input_claim=input_claim,
        reference_binding=binding,
        formula=formula,
        output_claim_id=output_claim_id,
    )


def _has_reference_search_obligation(report: ValidationReport) -> bool:
    return any(
        obligation.kind == "reference_search_required"
        for obligation in report.validation_requirements
    )


def _binding_for(
    bindings: tuple[CanonicalReference, ...],
    binding_id: str,
) -> CanonicalReference | None:
    for binding in reversed(bindings):
        if binding.binding_id == binding_id:
            return binding
    return None


__all__ = ["resolve_reference_grounded_calculation"]
