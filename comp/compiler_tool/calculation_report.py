from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.calculations import CalculationFormula, CalculationResult
from comp.compiler_tool.models import CompileReport, ProofObligation


def apply_calculation_result(
    report: CompileReport,
    result: CalculationResult,
    *,
    output_claim_id: str,
    formula: CalculationFormula,
) -> CompileReport:
    if result.status == "calculated" and result.derived_claim is not None:
        return replace(
            report,
            derived_claims=(*report.derived_claims, result.derived_claim),
            can_project_public_row=False,
        )

    reason = result.reason or "calculation_blocked"
    obligation = ProofObligation(
        kind="calculation_blocked",
        field=formula.output_field,
        reason=reason,
        obligation_id=(
            f"calculation:{formula.formula_id}:{output_claim_id}:{reason}"
        ),
        claim_id=output_claim_id,
        blocking=True,
    )
    return replace(
        report,
        status="blocked",
        obligations=_append_unique(report.obligations, obligation),
        can_project_public_row=False,
    )


def _append_unique(
    obligations: tuple[ProofObligation, ...],
    obligation: ProofObligation,
) -> tuple[ProofObligation, ...]:
    if obligation in obligations:
        return obligations
    return (*obligations, obligation)


__all__ = ["apply_calculation_result"]
