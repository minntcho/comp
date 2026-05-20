from dataclasses import replace

import pytest

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
from tests.support.persistence_cases import claim_envelope, receipt_projection_case


def test_artifact_store_records_envelopes_by_id_idempotently():
    store = InMemoryArtifactStore()
    envelope = claim_envelope(value=1200)

    assert store.record(envelope) == envelope
    assert store.record(envelope) == envelope

    assert store.get("artifact:claim:1") == envelope
    assert store.envelopes() == (envelope,)


def test_artifact_store_rejects_same_id_with_different_body_digest():
    store = InMemoryArtifactStore()
    envelope = claim_envelope(value=1200)
    changed = claim_envelope(value=1201)

    store.record(envelope)

    with pytest.raises(ArtifactConflict, match="artifact:claim:1"):
        store.record(changed)

    assert store.get("artifact:claim:1") == envelope


def test_artifact_store_rejects_envelope_when_body_does_not_match_digest():
    store = InMemoryArtifactStore()
    envelope = claim_envelope(value=1200)
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
    receipt = receipt_projection_case(amount=100).receipt

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
    receipt = receipt_projection_case(amount=100).receipt
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
    case = receipt_projection_case(amount=100)

    row = verify_materialized_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
    )

    assert row == case.public_row


def test_materialized_public_projection_blocks_tampered_values_or_extra_fields():
    case = receipt_projection_case(amount=100)

    with pytest.raises(ProjectionReplayBlocked, match="cannot be replayed"):
        verify_materialized_public_projection(
            {"site": "plant-a", "amount": 999999},
            case.projection,
            receipt=case.receipt,
        )

    with pytest.raises(ProjectionReplayBlocked, match="receipt-authorized view"):
        verify_materialized_public_projection(
            {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
            case.projection,
            receipt=case.receipt,
        )
