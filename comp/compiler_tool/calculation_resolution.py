from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.calculations import CalculationRequirement
from comp.compiler_tool.models import ValidationReport, ValidationRequirement


def plan_calculation_resolution(report: ValidationReport) -> ValidationReport:
    follow_ups = tuple(
        follow_up
        for obligation in report.obligations
        for follow_up in _follow_up_obligations(obligation)
    )
    if not follow_ups:
        return report

    obligations = report.obligations
    for follow_up in follow_ups:
        if follow_up not in obligations:
            obligations = (*obligations, follow_up)

    return replace(
        report,
        obligations=obligations,
        can_build_public_output=False,
    )


def _follow_up_obligations(
    obligation: ValidationRequirement,
) -> tuple[ValidationRequirement, ...]:
    requirement = obligation.calculation_requirement
    if obligation.kind != "calculation_blocked" or requirement is None:
        return ()

    kind = _follow_up_kind(requirement)
    if kind is None:
        return ()

    return (
        ValidationRequirement(
            kind=kind,
            field=obligation.field,
            reason=requirement.reason,
            obligation_id=_follow_up_id(requirement, kind),
            claim_id=requirement.output_claim_id,
            blocking=True,
            calculation_requirement=requirement,
        ),
    )


def _follow_up_kind(requirement: CalculationRequirement) -> str | None:
    if requirement.reason == "unknown_reference":
        return "reference_search_required"
    if requirement.reason == "missing_factor_value":
        return "reference_context_required"
    if requirement.reason in {
        "unit_mismatch",
        "output_unit_mismatch",
        "non_numeric_input",
    }:
        return "find_context"
    return None


def _follow_up_id(requirement: CalculationRequirement, kind: str) -> str:
    return f"resolve:{requirement.formula_id}:{requirement.output_claim_id}:{kind}"


__all__ = ["plan_calculation_resolution"]
