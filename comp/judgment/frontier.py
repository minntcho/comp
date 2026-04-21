from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CandidateSummary:
    candidate_id: str
    positive_evidence: float = 0.0
    negative_evidence: float = 0.0
    hazard_count: int = 0
    specificity: int = 0
    provenance_depth: int = 0


def dominates(left: CandidateSummary, right: CandidateSummary) -> bool:
    non_worse = (
        left.positive_evidence >= right.positive_evidence
        and left.negative_evidence <= right.negative_evidence
        and left.hazard_count <= right.hazard_count
        and left.specificity >= right.specificity
        and left.provenance_depth >= right.provenance_depth
    )
    strictly_better = (
        left.positive_evidence > right.positive_evidence
        or left.negative_evidence < right.negative_evidence
        or left.hazard_count < right.hazard_count
        or left.specificity > right.specificity
        or left.provenance_depth > right.provenance_depth
    )
    return non_worse and strictly_better


def frontier(summaries: Iterable[CandidateSummary]) -> list[CandidateSummary]:
    items = list(summaries)
    out: list[CandidateSummary] = []
    for item in items:
        if any(dominates(other, item) for other in items if other != item):
            continue
        out.append(item)
    return sorted(out, key=lambda item: item.candidate_id)


def winner_or_none(summaries: Iterable[CandidateSummary]) -> str | None:
    front = frontier(summaries)
    if len(front) != 1:
        return None
    return front[0].candidate_id


def needs_review(summaries: Iterable[CandidateSummary]) -> bool:
    return len(frontier(summaries)) > 1


__all__ = [
    "CandidateSummary",
    "dominates",
    "frontier",
    "winner_or_none",
    "needs_review",
]
