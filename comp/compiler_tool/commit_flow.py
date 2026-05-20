from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from comp.compiler_tool.commit_package import CommitPackage, build_commit_package
from comp.compiler_tool.governance import GovernanceDecision, decide_governance
from comp.compiler_tool.models import CompileReport
from comp.compiler_tool.receipt_builder import build_commit_receipt
from comp.judgment.receipts import CommitReceipt


@dataclass(frozen=True)
class CommitPreparation:
    package: CommitPackage
    decision: GovernanceDecision
    receipt: CommitReceipt | None = None

    @property
    def can_project_public_row(self) -> bool:
        return self.receipt is not None


def prepare_commit(
    report: CompileReport,
    *,
    subject_id: str,
    public_row_id: str,
    projection_id: str,
    package_id: str | None = None,
    decision_id: str | None = None,
    profile_id: str | None = None,
    semantic_judgment_ids: Iterable[str] = (),
) -> CommitPreparation:
    package = build_commit_package(
        report,
        subject_id=subject_id,
        package_id=package_id,
        profile_id=profile_id,
        semantic_judgment_ids=semantic_judgment_ids,
    )
    decision = decide_governance(package, decision_id=decision_id)
    receipt = None
    if decision.can_issue_commit_receipt and package.complete:
        receipt = build_commit_receipt(
            package,
            decision,
            public_row_id=public_row_id,
            projection_id=projection_id,
        )
    return CommitPreparation(package=package, decision=decision, receipt=receipt)


__all__ = ["CommitPreparation", "prepare_commit"]
