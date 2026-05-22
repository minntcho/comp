from __future__ import annotations

from comp.compiler_tool.commit_package import ReviewPackage
from comp.compiler_tool.governance import ReviewDecision
from comp.judgment.receipts import (
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
)


class ReceiptBuildBlocked(RuntimeError):
    """Raised when a review decision cannot mint a public-output receipt."""


def build_public_output_receipt(
    package: ReviewPackage,
    decision: ReviewDecision,
    *,
    public_row_id: str,
    projection_id: str,
) -> PublicOutputReceipt:
    _validate_receipt_inputs(package, decision, projection_id=projection_id)
    authorized_fields = _authorized_fields(package)
    citations = _receipt_citations(
        package,
        decision,
        projection_id=projection_id,
        authorized_fields=authorized_fields,
    )
    return PublicOutputReceipt(
        draft_id=package.package_id,
        winner_receipt_ids=(decision.decision_id,),
        barrier_snapshot=citations.to_barrier_snapshot(),
        public_row_id=public_row_id,
        projection_id=projection_id,
        authorized_fields=authorized_fields,
        citations=citations,
    )


build_commit_receipt = build_public_output_receipt


def _validate_receipt_inputs(
    package: ReviewPackage,
    decision: ReviewDecision,
    *,
    projection_id: str,
) -> None:
    if not projection_id:
        raise ReceiptBuildBlocked("Public-output receipt requires an output id.")
    if decision.package_id != package.package_id:
        raise ReceiptBuildBlocked("Public-output receipt package mismatch.")
    if decision.subject_id != package.subject_id:
        raise ReceiptBuildBlocked("Public-output receipt subject mismatch.")
    if not decision.can_issue_commit_receipt:
        raise ReceiptBuildBlocked("Public-output receipt requires a commit decision.")
    if not package.complete:
        raise ReceiptBuildBlocked("Public-output receipt requires a complete package.")


def _receipt_citations(
    package: ReviewPackage,
    decision: ReviewDecision,
    *,
    projection_id: str,
    authorized_fields: tuple[str, ...],
) -> PublicOutputReceiptCitations:
    return PublicOutputReceiptCitations(
        governance_decision_id=decision.decision_id,
        governance_status=decision.status,
        governance_reasons=decision.reasons,
        commit_package_id=package.package_id,
        commit_package_complete=package.complete,
        subject_id=package.subject_id,
        projection_id=projection_id,
        authorized_fields=authorized_fields,
        profile_id=package.profile_id,
        report_status=package.report_status,
        checked_claim_fields=package.checked_claim_fields,
        checked_claim_witness_ids=package.checked_claim_witness_ids,
        semantic_judgment_ids=package.semantic_judgment_ids,
        reference_binding_ids=package.reference_binding_ids,
        derived_claim_fields=package.derived_claim_fields,
        derived_claim_ids=package.derived_claim_ids,
        calculation_trace_ids=package.calculation_trace_ids,
        formula_ids=package.formula_ids,
        resolved_obligation_ids=package.resolved_obligation_ids,
        open_obligation_ids=package.open_obligation_ids,
        hazard_ids=package.hazard_ids,
        projection_value_commitments=package.projection_value_commitments,
        dependency_fingerprints=package.dependency_fingerprints,
    )


def _authorized_fields(package: ReviewPackage) -> tuple[str, ...]:
    return _unique((*package.checked_claim_fields, *package.derived_claim_fields))


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    seen = set()
    unique_values = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return tuple(unique_values)


__all__ = [
    "ReceiptBuildBlocked",
    "build_public_output_receipt",
    "build_commit_receipt",
]
