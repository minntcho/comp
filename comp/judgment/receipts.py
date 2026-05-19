from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SelectionReceipt:
    bundle_id: str
    frontier_ids: tuple[str, ...]
    winner_id: str | None
    bundle_version: int
    reason: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CommitReceiptCitations:
    governance_decision_id: str
    governance_status: str
    governance_reasons: tuple[str, ...]
    commit_package_id: str
    commit_package_complete: bool
    subject_id: str
    profile_id: str | None
    report_status: str
    checked_claim_fields: tuple[str, ...]
    checked_claim_witness_ids: tuple[str, ...]
    semantic_judgment_ids: tuple[str, ...]
    reference_binding_ids: tuple[str, ...]
    derived_claim_ids: tuple[str, ...]
    calculation_trace_ids: tuple[str, ...]
    formula_ids: tuple[str, ...]
    resolved_obligation_ids: tuple[str, ...]
    open_obligation_ids: tuple[str, ...]
    hazard_ids: tuple[str, ...]

    def to_barrier_snapshot(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("governance_decision_id", self.governance_decision_id),
            ("governance_status", self.governance_status),
            ("governance_reasons", self.governance_reasons),
            ("commit_package_id", self.commit_package_id),
            ("commit_package_complete", self.commit_package_complete),
            ("subject_id", self.subject_id),
            ("profile_id", self.profile_id),
            ("report_status", self.report_status),
            ("checked_claim_fields", self.checked_claim_fields),
            ("checked_claim_witness_ids", self.checked_claim_witness_ids),
            ("semantic_judgment_ids", self.semantic_judgment_ids),
            ("reference_binding_ids", self.reference_binding_ids),
            ("derived_claim_ids", self.derived_claim_ids),
            ("calculation_trace_ids", self.calculation_trace_ids),
            ("formula_ids", self.formula_ids),
            ("resolved_obligation_ids", self.resolved_obligation_ids),
            ("open_obligation_ids", self.open_obligation_ids),
            ("hazard_ids", self.hazard_ids),
        )


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    draft_id: str
    winner_receipt_ids: tuple[str, ...]
    barrier_snapshot: tuple[tuple[str, Any], ...]
    public_row_id: str
    citations: CommitReceiptCitations | None = None


__all__ = ["SelectionReceipt", "CommitReceipt", "CommitReceiptCitations"]
