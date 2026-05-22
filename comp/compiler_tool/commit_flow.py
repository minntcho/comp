from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from comp.compiler_tool.commit_package import ReviewPackage, build_commit_package
from comp.compiler_tool.governance import ReviewDecision, decide_governance
from comp.compiler_tool.models import CompileReport
from comp.compiler_tool.receipt_builder import build_public_output_receipt
from comp.judgment.receipts import DependencyFingerprint, PublicOutputReceipt


@dataclass(frozen=True)
class CommitPreparation:
    package: ReviewPackage
    decision: ReviewDecision
    receipt: PublicOutputReceipt | None = None

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
    dependency_fingerprints: Iterable[DependencyFingerprint] = (),
) -> CommitPreparation:
    package = build_commit_package(
        report,
        subject_id=subject_id,
        package_id=package_id,
        profile_id=profile_id,
        semantic_judgment_ids=semantic_judgment_ids,
        dependency_fingerprints=dependency_fingerprints,
    )
    decision = decide_governance(package, decision_id=decision_id)
    receipt = None
    if decision.can_issue_commit_receipt and package.complete:
        receipt = build_public_output_receipt(
            package,
            decision,
            public_row_id=public_row_id,
            projection_id=projection_id,
        )
    return CommitPreparation(package=package, decision=decision, receipt=receipt)


__all__ = ["CommitPreparation", "prepare_commit"]
