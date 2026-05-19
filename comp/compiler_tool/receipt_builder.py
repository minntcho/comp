from __future__ import annotations

from comp.compiler_tool.commit_package import CommitPackage
from comp.compiler_tool.governance import GovernanceDecision
from comp.judgment.receipts import CommitReceipt


class ReceiptBuildBlocked(RuntimeError):
    """Raised when a governance decision cannot mint a commit receipt."""


def build_commit_receipt(
    package: CommitPackage,
    decision: GovernanceDecision,
    *,
    public_row_id: str,
) -> CommitReceipt:
    _validate_receipt_inputs(package, decision)
    return CommitReceipt(
        draft_id=package.package_id,
        winner_receipt_ids=(decision.decision_id,),
        barrier_snapshot=_barrier_snapshot(package, decision),
        public_row_id=public_row_id,
    )


def _validate_receipt_inputs(
    package: CommitPackage,
    decision: GovernanceDecision,
) -> None:
    if decision.package_id != package.package_id:
        raise ReceiptBuildBlocked("Commit receipt package mismatch.")
    if decision.subject_id != package.subject_id:
        raise ReceiptBuildBlocked("Commit receipt subject mismatch.")
    if not decision.can_issue_commit_receipt:
        raise ReceiptBuildBlocked("Commit receipt requires a commit decision.")
    if not package.complete:
        raise ReceiptBuildBlocked("Commit receipt requires a complete package.")


def _barrier_snapshot(
    package: CommitPackage,
    decision: GovernanceDecision,
) -> tuple[tuple[str, object], ...]:
    return (
        ("governance_decision_id", decision.decision_id),
        ("governance_status", decision.status),
        ("governance_reasons", decision.reasons),
        ("commit_package_id", package.package_id),
        ("commit_package_complete", package.complete),
        ("subject_id", package.subject_id),
        ("profile_id", package.profile_id),
        ("report_status", package.report_status),
        ("checked_claim_fields", package.checked_claim_fields),
        ("checked_claim_witness_ids", package.checked_claim_witness_ids),
        ("semantic_judgment_ids", package.semantic_judgment_ids),
        ("reference_binding_ids", package.reference_binding_ids),
        ("derived_claim_ids", package.derived_claim_ids),
        ("calculation_trace_ids", package.calculation_trace_ids),
        ("formula_ids", package.formula_ids),
        ("resolved_obligation_ids", package.resolved_obligation_ids),
        ("open_obligation_ids", package.open_obligation_ids),
        ("hazard_ids", package.hazard_ids),
    )


__all__ = ["ReceiptBuildBlocked", "build_commit_receipt"]
