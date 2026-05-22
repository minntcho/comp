from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.calculation_report import apply_calculation_result
from comp.compiler_tool.calculations import (
    CalculationFormula,
    CalculationInput,
    CalculatedClaim,
    calculate_derived_claim,
)
from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.compiler_tool.reference_db import ReferenceCatalog
from comp.compiler_tool.references import CanonicalReference
from comp.compiler_tool.report_status import with_recomputed_status


def retry_blocked_calculation(
    report: ValidationReport,
    catalog: ReferenceCatalog,
    *,
    input_claim: CalculationInput,
    reference_binding: CanonicalReference,
    formula: CalculationFormula,
    output_claim_id: str,
) -> ValidationReport:
    result = calculate_derived_claim(
        output_claim_id=output_claim_id,
        input_claim=input_claim,
        reference_binding=reference_binding,
        catalog=catalog,
        formula=formula,
    )
    if result.status == "calculated" and result.derived_claim is not None:
        open_obligations, resolved = _split_matching_calculation_obligations(
            report.obligations,
            formula=formula,
            output_claim_id=output_claim_id,
        )
        base_report = replace(
            report,
            obligations=open_obligations,
            resolved_obligations=_append_unique_obligations(
                report.resolved_obligations,
                resolved,
            ),
            can_build_public_output=False,
        )
        return with_recomputed_status(
            replace(
                base_report,
                derived_claims=_append_unique_derived_claim(
                    base_report.derived_claims,
                    result.derived_claim,
                ),
                can_build_public_output=False,
            )
        )

    return apply_calculation_result(
        report,
        result,
        output_claim_id=output_claim_id,
        formula=formula,
    )


def _split_matching_calculation_obligations(
    obligations: tuple[ValidationRequirement, ...],
    *,
    formula: CalculationFormula,
    output_claim_id: str,
) -> tuple[tuple[ValidationRequirement, ...], tuple[ValidationRequirement, ...]]:
    open_obligations: list[ValidationRequirement] = []
    resolved: list[ValidationRequirement] = []
    for obligation in obligations:
        if _matches_calculation_obligation(
            obligation,
            formula=formula,
            output_claim_id=output_claim_id,
        ):
            resolved.append(obligation)
        else:
            open_obligations.append(obligation)
    return tuple(open_obligations), tuple(resolved)


def _matches_calculation_obligation(
    obligation: ValidationRequirement,
    *,
    formula: CalculationFormula,
    output_claim_id: str,
) -> bool:
    if obligation.kind != "calculation_blocked":
        return False

    requirement = obligation.calculation_requirement
    if requirement is not None:
        return (
            requirement.formula_id == formula.formula_id
            and requirement.output_claim_id == output_claim_id
        )

    return (
        obligation.field == formula.output_field
        and obligation.claim_id == output_claim_id
    )


def _append_unique_obligations(
    existing: tuple[ValidationRequirement, ...],
    additions: tuple[ValidationRequirement, ...],
) -> tuple[ValidationRequirement, ...]:
    result = existing
    for obligation in additions:
        if obligation not in result:
            result = (*result, obligation)
    return result


def _append_unique_derived_claim(
    existing: tuple[CalculatedClaim, ...],
    addition: CalculatedClaim,
) -> tuple[CalculatedClaim, ...]:
    if any(claim.claim_id == addition.claim_id for claim in existing):
        return existing
    return (*existing, addition)


__all__ = ["retry_blocked_calculation"]
