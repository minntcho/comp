from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from comp.compiler_tool.commit_package import ReviewPackage

GovernanceStatus = Literal["commit", "hold", "reject"]


@dataclass(frozen=True)
class ReviewDecision:
    decision_id: str
    package_id: str
    subject_id: str
    status: GovernanceStatus
    reasons: tuple[str, ...] = field(default_factory=tuple)
    profile_id: str | None = None

    @property
    def can_issue_commit_receipt(self) -> bool:
        return self.status == "commit"

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


GovernanceDecision = ReviewDecision


def decide_governance(
    package: ReviewPackage,
    *,
    decision_id: str | None = None,
) -> ReviewDecision:
    status, reasons = _evaluate_package(package)
    return ReviewDecision(
        decision_id=decision_id or f"governance-decision:{package.package_id}",
        package_id=package.package_id,
        subject_id=package.subject_id,
        status=status,
        reasons=reasons,
        profile_id=package.profile_id,
    )


def _evaluate_package(
    package: ReviewPackage,
) -> tuple[GovernanceStatus, tuple[str, ...]]:
    if package.complete:
        return "commit", ("commit_package_complete",)

    reasons = _incomplete_reasons(package)
    if package.open_obligation_ids or package.hazard_ids:
        return "hold", reasons
    if package.report_status == "blocked":
        return "reject", reasons
    return "hold", reasons


def _incomplete_reasons(package: ReviewPackage) -> tuple[str, ...]:
    reasons = []
    if package.report_status != "accepted":
        reasons.append(f"report_status:{package.report_status}")
    reasons.extend(
        f"open_obligation:{obligation_id}"
        for obligation_id in package.open_obligation_ids
    )
    reasons.extend(package.hazard_ids)
    if not reasons:
        reasons.append("commit_package_incomplete")
    return tuple(reasons)


__all__ = [
    "ReviewDecision",
    "GovernanceDecision",
    "GovernanceStatus",
    "decide_governance",
]
