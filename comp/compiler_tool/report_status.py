from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool.models import ValidationReport, CompileStatus


def recompute_report_status(report: ValidationReport) -> CompileStatus:
    if report.failed_claims:
        return "blocked"
    if any(
        obligation.kind == "calculation_blocked" and obligation.blocking
        for obligation in report.validation_requirements
    ):
        return "blocked"
    if report.hazards:
        return "review_required"
    if any(
        obligation.kind == "semantic_judgment_required" and obligation.blocking
        for obligation in report.validation_requirements
    ):
        return "review_required"
    if report.unchecked_areas:
        return "unchecked"
    if report.unknowns:
        return "underconstrained"
    if any(obligation.blocking for obligation in report.validation_requirements):
        return "review_required"
    return "accepted"


def with_recomputed_status(report: ValidationReport) -> ValidationReport:
    return replace(report, status=recompute_report_status(report))


__all__ = ["recompute_report_status", "with_recomputed_status"]
