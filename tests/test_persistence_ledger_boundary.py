from dataclasses import replace

import pytest

from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    ProjectionSpec,
    ProjectionValueCommitment,
)
from comp.persistence import (
    ArtifactConflict,
    ArtifactEnvelope,
    ArtifactIntegrityError,
    InMemoryArtifactStore,
    InMemoryReceiptLedger,
    ProjectionReplayBlocked,
    ReceiptConflict,
    verify_materialized_public_projection,
)


def test_artifact_store_records_envelopes_by_id_idempotently():
    store = InMemoryArtifactStore()
    envelope = _claim_envelope(value=1200)

    assert store.record(envelope) == envelope
    assert store.record(envelope) == envelope

    assert store.get("artifact:claim:1") == envelope
    assert store.envelopes() == (envelope,)


def test_artifact_store_rejects_same_id_with_different_body_digest():
    store = InMemoryArtifactStore()
    envelope = _claim_envelope(value=1200)
    changed = _claim_envelope(value=1201)

    store.record(envelope)

    with pytest.raises(ArtifactConflict, match="artifact:claim:1"):
        store.record(changed)

    assert store.get("artifact:claim:1") == envelope


def test_artifact_store_rejects_envelope_when_body_does_not_match_digest():
    store = InMemoryArtifactStore()
    envelope = _claim_envelope(value=1200)
    tampered = ArtifactEnvelope(
        artifact_id=envelope.artifact_id,
        artifact_kind=envelope.artifact_kind,
        schema_version=envelope.schema_version,
        body_digest=envelope.body_digest,
        body={"field": "electricity_kwh", "value": 999999},
    )

    with pytest.raises(ArtifactIntegrityError, match="body digest"):
        store.record(tampered)


def test_receipt_ledger_records_commit_receipt_as_append_only_root():
    ledger = InMemoryReceiptLedger()
    receipt = _receipt(amount=100)

    assert ledger.record(receipt) == receipt
    assert ledger.record(receipt) == receipt

    assert ledger.get(
        public_row_id="public-row-1",
        projection_id="public-row",
        draft_id="draft-1",
    ) == receipt
    assert ledger.receipts() == (receipt,)


def test_receipt_ledger_rejects_mutating_existing_receipt_root():
    ledger = InMemoryReceiptLedger()
    receipt = _receipt(amount=100)
    changed = replace(
        receipt,
        authorized_fields=("site",),
        barrier_snapshot=(("changed_after_commit", True),),
    )

    ledger.record(receipt)

    with pytest.raises(ReceiptConflict, match="public-row-1"):
        ledger.record(changed)

    assert ledger.receipts() == (receipt,)


def test_materialized_public_projection_is_a_receipt_verified_view():
    projection = ProjectionSpec("public-row", ("site", "amount"))
    receipt = _receipt(amount=100)

    row = verify_materialized_public_projection(
        {"site": "plant-a", "amount": 100},
        projection,
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


def test_materialized_public_projection_blocks_tampered_values_or_extra_fields():
    projection = ProjectionSpec("public-row", ("site", "amount"))
    receipt = _receipt(amount=100)

    with pytest.raises(ProjectionReplayBlocked, match="cannot be replayed"):
        verify_materialized_public_projection(
            {"site": "plant-a", "amount": 999999},
            projection,
            receipt=receipt,
        )

    with pytest.raises(ProjectionReplayBlocked, match="receipt-authorized view"):
        verify_materialized_public_projection(
            {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
            projection,
            receipt=receipt,
        )


def _claim_envelope(*, value: int) -> ArtifactEnvelope:
    return ArtifactEnvelope.from_body(
        artifact_id="artifact:claim:1",
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": value},
    )


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
