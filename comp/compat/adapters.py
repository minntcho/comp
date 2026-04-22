from __future__ import annotations

from typing import Iterable

from comp.compat.artifacts import CanonicalRowArtifact, ClaimArtifact, PartialFrameArtifact, RoleLineageArtifact, RoleSlotArtifact
from comp.judgment import CandidateSummary, CommitReceipt, CommitSpec, DraftSnapshot, SelectionReceipt, frontier, winner_or_none

_MODE_SPECIFICITY = {
    "explicit": 4,
    "inherited": 3,
    "backward_inferred": 2,
    "derived": 1,
}


def _score_total(claim: ClaimArtifact) -> float:
    data = claim.metadata.get("repair_score")
    if isinstance(data, dict) and "total" in data:
        return float(data["total"])
    return float(claim.confidence)


def summarize_claim_candidate(claim: ClaimArtifact) -> CandidateSummary:
    negative = float(len(set(claim.reason_codes)))
    if claim.candidate_state in {"frozen", "rejected"}:
        negative += 1.0

    return CandidateSummary(
        candidate_id=claim.claim_id,
        positive_evidence=_score_total(claim),
        negative_evidence=negative,
        hazard_count=len(set(claim.reason_codes)),
        specificity=_MODE_SPECIFICITY.get(claim.extraction_mode, 0),
        provenance_depth=max(1, len(claim.evidence_ids)),
    )


def slot_candidate_ids(slot: RoleSlotArtifact) -> list[str]:
    ordered = []
    for cid in [slot.active_claim_id, *slot.shadow_claim_ids, *slot.frozen_claim_ids, *slot.rejected_claim_ids]:
        if cid and cid not in ordered:
            ordered.append(cid)
    return ordered


def slot_candidate_summaries(slot: RoleSlotArtifact, claims_by_id: dict[str, ClaimArtifact]) -> list[CandidateSummary]:
    out: list[CandidateSummary] = []
    for cid in slot_candidate_ids(slot):
        claim = claims_by_id.get(cid)
        if claim is None:
            continue
        out.append(summarize_claim_candidate(claim))
    return out


def build_slot_selection_receipt(
    *,
    frame: PartialFrameArtifact,
    role_name: str,
    slot: RoleSlotArtifact,
    claims_by_id: dict[str, ClaimArtifact],
    bundle_version: int,
) -> SelectionReceipt:
    summaries = slot_candidate_summaries(slot, claims_by_id)
    front = frontier(summaries)
    return SelectionReceipt(
        bundle_id=f"{frame.frame_id}:{role_name}",
        frontier_ids=tuple(item.candidate_id for item in front),
        winner_id=winner_or_none(summaries),
        bundle_version=bundle_version,
        reason=tuple(sorted(set(slot.reason_codes))),
    )


def _resolved_bundle_names(row: CanonicalRowArtifact) -> frozenset[str]:
    resolved = set()
    if row.site_id is not None:
        resolved.add("site")
    if row.entity_id is not None:
        resolved.add("entity")
    if row.period is not None:
        resolved.add("period")
    if row.activity_type is not None:
        resolved.add("activity_type")
    if row.raw_amount is not None:
        resolved.add("raw_amount")
    if row.raw_unit is not None:
        resolved.add("raw_unit")
    if row.standardized_amount is not None:
        resolved.add("standardized_amount")
    if row.standardized_unit is not None:
        resolved.add("standardized_unit")
    if row.scope_category is not None:
        resolved.add("scope_category")
    return frozenset(resolved)


def _lineage_count(lineage: RoleLineageArtifact) -> int:
    return (
        len(lineage.direct)
        + len(lineage.inherited)
        + len(lineage.backward_inferred)
        + len(lineage.derived)
        + len(lineage.contradicted_by)
    )


def draft_snapshot_from_row(row: CanonicalRowArtifact) -> DraftSnapshot:
    provenance_edges = len(row.source_fragment_ids) + sum(_lineage_count(l) for l in row.lineage.values())
    return DraftSnapshot(
        draft_id=row.frame_id,
        resolved_bundles=_resolved_bundle_names(row),
        active_hazards=frozenset(row.error_codes),
        fresh=not bool(row.metadata.get("stale_selection", False)),
        provenance_edges=provenance_edges,
    )


def commit_spec_from_row(row: CanonicalRowArtifact, *, block_on_any_error: bool = True) -> CommitSpec:
    return CommitSpec(
        commit_id=f"{row.frame_type}:commit",
        required_bundles=tuple(),
        blocking_hazards=tuple(sorted(set(row.error_codes))) if block_on_any_error else tuple(),
        min_provenance_edges=0,
        require_fresh=True,
    )


def build_commit_receipt(
    *,
    row: CanonicalRowArtifact,
    decision_id: str,
    matched_rule_keys: Iterable[str] = (),
) -> CommitReceipt:
    snapshot = draft_snapshot_from_row(row)
    barrier_snapshot = (
        ("fresh", snapshot.fresh),
        ("active_hazard_count", len(snapshot.active_hazards)),
        ("provenance_edges", snapshot.provenance_edges),
    )
    return CommitReceipt(
        draft_id=row.frame_id,
        winner_receipt_ids=tuple(matched_rule_keys),
        barrier_snapshot=barrier_snapshot,
        public_row_id=row.row_id,
    )


__all__ = [
    "summarize_claim_candidate",
    "slot_candidate_ids",
    "slot_candidate_summaries",
    "build_slot_selection_receipt",
    "draft_snapshot_from_row",
    "commit_spec_from_row",
    "build_commit_receipt",
]
