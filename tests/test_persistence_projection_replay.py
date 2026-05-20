import pytest

from comp.persistence import (
    ArtifactEnvelope,
    ArtifactRef,
    ProjectionReplayBlocked,
    ProjectionReplayReport,
    ReceiptLedgerKey,
    receipt_artifact_refs,
    replay_public_projection,
)
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)


def test_replay_public_projection_explains_row_from_receipt_and_artifacts():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    report = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )

    assert isinstance(report, ProjectionReplayReport)
    assert report.receipt_key == ReceiptLedgerKey(
        public_row_id="public-row-1",
        projection_id="public-row",
        draft_id="draft-1",
    )
    assert report.public_row == case.public_row
    assert report.artifact_refs == receipt_artifact_refs(case.receipt)
    assert ArtifactRef("package-1", "commit_package") in report.artifact_refs
    assert ArtifactRef("decision-1", "governance_decision") in report.artifact_refs
    assert (
        ArtifactRef("checked_claim:amount:span-amount", "checked_claim")
        in report.artifact_refs
    )
    assert dict(report.artifact_digests)["package-1"].startswith("sha256:")


def test_replay_blocks_when_required_artifact_is_missing():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
        skip=ArtifactRef("decision-1", "governance_decision"),
    )

    with pytest.raises(ProjectionReplayBlocked, match="missing artifact"):
        replay_public_projection(
            case.source_values,
            case.projection,
            receipt=case.receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_required_artifact_kind_mismatches():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
        override=ArtifactEnvelope.from_body(
            artifact_id="decision-1",
            artifact_kind="commit_package",
            schema_version="v1",
            body={"status": "commit"},
        ),
    )

    with pytest.raises(ProjectionReplayBlocked, match="artifact kind"):
        replay_public_projection(
            case.source_values,
            case.projection,
            receipt=case.receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_stored_artifact_body_drifts_after_recording():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    artifacts.get("package-1").body["complete"] = False

    with pytest.raises(ProjectionReplayBlocked, match="body digest"):
        replay_public_projection(
            case.source_values,
            case.projection,
            receipt=case.receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_committed_source_artifact_value_drifts():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
        override=ArtifactEnvelope.from_body(
            artifact_id="checked_claim:amount:span-amount",
            artifact_kind="checked_claim",
            schema_version="v1",
            body={
                "claim_id": "checked_claim:amount:span-amount",
                "field": "amount",
                "value": 999999,
            },
        ),
    )

    with pytest.raises(ProjectionReplayBlocked, match="value commitment mismatch"):
        replay_public_projection(
            case.source_values,
            case.projection,
            receipt=case.receipt,
            artifacts=artifacts,
        )


def test_replay_blocks_when_materialized_row_no_longer_matches_receipt():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    with pytest.raises(ProjectionReplayBlocked, match="cannot be replayed"):
        replay_public_projection(
            {"site": "plant-a", "amount": 999999},
            case.projection,
            receipt=case.receipt,
            artifacts=artifacts,
        )
