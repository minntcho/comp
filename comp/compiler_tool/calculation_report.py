from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.calculations import (
    CalculationFormula,
    CalculationRequirement,
    CalculationResult,
)
from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.compiler_tool.report_status import with_recomputed_status


def apply_calculation_result(
    report: ValidationReport,
    result: CalculationResult,
    *,
    output_claim_id: str,
    formula: CalculationFormula,
) -> ValidationReport:
    if result.status == "calculated" and result.derived_claim is not None:
        return with_recomputed_status(
            replace(
                report,
                calculated_claims=(*report.calculated_claims, result.derived_claim),
                can_build_public_output=False,
            )
        )

    reason = result.reason or "calculation_blocked"
    requirement = result.requirement or CalculationRequirement(
        reason=reason,
        formula_id=formula.formula_id,
        output_claim_id=output_claim_id,
    )
    obligation = ValidationRequirement(
        kind="calculation_blocked",
        field=formula.output_field,
        reason=reason,
        requirement_id=(
            f"calculation:{formula.formula_id}:{output_claim_id}:{reason}"
        ),
        claim_id=output_claim_id,
        blocking=True,
        calculation_requirement=requirement,
    )
    return with_recomputed_status(
        replace(
            report,
            validation_requirements=_append_unique(report.validation_requirements, obligation),
            can_build_public_output=False,
        )
    )


def _append_unique(
    obligations: tuple[ValidationRequirement, ...],
    obligation: ValidationRequirement,
) -> tuple[ValidationRequirement, ...]:
    if obligation in obligations:
        return obligations
    return (*obligations, obligation)


__all__ = ["apply_calculation_result"]
