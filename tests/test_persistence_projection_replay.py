import pytest

from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    ProjectionSpec,
    ProjectionValueCommitment,
)
from comp.persistence import (
    ArtifactEnvelope,
    ArtifactRef,
    InMemoryArtifactStore,
    ProjectionReplayBlocked,
    ProjectionReplayReport,
    ReceiptLedgerKey,
    receipt_artifact_refs,
    replay_public_projection,
)


def test_replay_public_projection_explains_row_from_receipt_and_artifacts():
    receipt = _receipt(amount=100)
    artifacts = _artifact_store_for(receipt)
    projection = ProjectionSpec("public-row", ("site", "amount"))

    report = replay_public_projection(
        {"site": "plant-a", "amount": 100},
        projection,
        receipt=receipt,
        artifacts=artifacts,
    )

    assert isinstance(report, ProjectionReplayReport)
    assert report.receipt_key == ReceiptLedgerKey(
        public_row_id="public-row-1",
        projection_id="public-row",
        draft_id="draft-1",
    )
    assert report.public_row == {"site": "plant-a", "amount": 100}
    assert report.artifact_refs == receipt_artifact_refs(receipt)
    assert ArtifactRef("package-1", "commit_package") in report.artifact_refs
    assert ArtifactRef("decision-1", "governance_decision") in report.artifact_refs
    assert (
        ArtifactRef("checked_claim:amount:span-amount", "checked_claim")
        in report.artifact_refs
    )
    assert dict(report.artifact_digests)["package-1"].startswith("sha256:")


def test_replay_blocks_when_required_artifact_is_missing():
    receipt = _receipt(amount=100)
    artifacts = _artifact_store_for(
        receipt,
        skip=ArtifactRef("decision-1", "governance_decision"),
    )
    projection = ProjectionSpec("public-row", ("site", "amount"))

    with pytest.raises(ProjectionReplayBlocked, match="missing artifact"):
        replay_public_projection(
            {"site": "plant-a", "amount": 100},
            projection,
            receipt=receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_required_artifact_kind_mismatches():
    receipt = _receipt(amount=100)
    artifacts = _artifact_store_for(
        receipt,
        override=ArtifactEnvelope.from_body(
            artifact_id="decision-1",
            artifact_kind="commit_package",
            schema_version="v1",
            body={"status": "commit"},
        ),
    )
    projection = ProjectionSpec("public-row", ("site", "amount"))

    with pytest.raises(ProjectionReplayBlocked, match="artifact kind"):
        replay_public_projection(
            {"site": "plant-a", "amount": 100},
            projection,
            receipt=receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_stored_artifact_body_drifts_after_recording():
    receipt = _receipt(amount=100)
    artifacts = _artifact_store_for(receipt)
    artifacts.get("package-1").body["complete"] = False
    projection = ProjectionSpec("public-row", ("site", "amount"))

    with pytest.raises(ProjectionReplayBlocked, match="body digest"):
        replay_public_projection(
            {"site": "plant-a", "amount": 100},
            projection,
            receipt=receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_materialized_row_no_longer_matches_receipt():
    receipt = _receipt(amount=100)
    artifacts = _artifact_store_for(receipt)
    projection = ProjectionSpec("public-row", ("site", "amount"))

    with pytest.raises(ProjectionReplayBlocked, match="cannot be replayed"):
        replay_public_projection(
            {"site": "plant-a", "amount": 999999},
            projection,
            receipt=receipt,
            artifacts=artifacts,
        )


def _artifact_store_for(
    receipt: CommitReceipt,
    *,
    skip: ArtifactRef | None = None,
    override: ArtifactEnvelope | None = None,
) -> InMemoryArtifactStore:
    store = InMemoryArtifactStore()
    for ref in receipt_artifact_refs(receipt):
        if ref == skip:
            continue
        if override is not None and override.artifact_id == ref.artifact_id:
            store.record(override)
            continue
        store.record(_artifact_for_ref(ref))
    return store


def _artifact_for_ref(ref: ArtifactRef) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id=ref.artifact_id,
        artifact_kind=ref.artifact_kind,
        schema_version="v1",
        body=_artifact_body_for_ref(ref),
    )


def _artifact_body_for_ref(ref: ArtifactRef) -> dict:
    if ref.artifact_kind == "commit_package":
        return {"package_id": ref.artifact_id, "complete": True}
    if ref.artifact_kind == "governance_decision":
        return {"decision_id": ref.artifact_id, "status": "commit"}
    if ref.artifact_kind == "checked_claim":
        return {"claim_id": ref.artifact_id, "field": "amount"}
    if ref.artifact_kind == "evidence_witness":
        return {"witness_id": ref.artifact_id, "source": "fixture"}
    raise AssertionError(f"Unexpected artifact ref in test: {ref}")


def _receipt(*, amount: int) -> CommitReceipt:
    commitments = (
        ProjectionValueCommitment.from_value(
            field="site",
            source_kind="checked_claim",
            source_id="checked_claim:site:span-site",
            value="plant-a",
        ),
        ProjectionValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:span-amount",
            value=amount,
        ),
    )
    citations = CommitReceiptCitations(
        governance_decision_id="decision-1",
        governance_status="commit",
        governance_reasons=("ready",),
        commit_package_id="package-1",
        commit_package_complete=True,
        subject_id="facility-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        profile_id=None,
        report_status="accepted",
        checked_claim_fields=("site", "amount"),
        checked_claim_witness_ids=("span-site", "span-amount"),
        semantic_judgment_ids=(),
        reference_binding_ids=(),
        derived_claim_fields=(),
        derived_claim_ids=(),
        calculation_trace_ids=(),
        formula_ids=(),
        resolved_obligation_ids=(),
        open_obligation_ids=(),
        hazard_ids=(),
        projection_value_commitments=commitments,
    )
    return CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("decision-1",),
        barrier_snapshot=citations.to_barrier_snapshot(),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=citations,
    )
