import pytest

from comp.persistence import (
    ArtifactMaterial,
    InMemoryArtifactStore,
    ReceiptEnvelopeSetBuildError,
    build_receipt_envelope_set,
    replay_public_projection,
)
from tests.support.persistence_cases import (
    artifact_body_for_ref,
    receipt_projection_case,
)


def _material_for_ref(ref, *, committed_values=None):
    return ArtifactMaterial(
        artifact_id=ref.artifact_id,
        artifact_kind=ref.artifact_kind,
        schema_version="v1",
        body=artifact_body_for_ref(ref, committed_values=committed_values),
    )


def _materials_for_receipt(receipt, *, committed_values=None):
    from comp.persistence import receipt_artifact_refs

    return tuple(
        _material_for_ref(ref, committed_values=committed_values)
        for ref in receipt_artifact_refs(receipt)
    )


def test_build_receipt_envelope_set_covers_receipt_refs_and_replays():
    case = receipt_projection_case(amount=100)
    materials = _materials_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    envelopes = build_receipt_envelope_set(case.receipt, materials)
    store = InMemoryArtifactStore()
    for envelope in envelopes:
        store.record(envelope)

    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=store,
    )

    assert {envelope.artifact_id for envelope in envelopes} == {
        ref.artifact_id for ref in replay.artifact_refs
    }
    assert replay.public_row == case.public_row


def test_build_receipt_envelope_set_records_to_store_when_requested():
    case = receipt_projection_case(amount=100)
    store = InMemoryArtifactStore()

    envelopes = build_receipt_envelope_set(
        case.receipt,
        _materials_for_receipt(case.receipt, committed_values=case.source_values),
        record_to=store,
    )

    assert tuple(store.envelopes()) == envelopes


def test_build_receipt_envelope_set_requires_receipt_citations():
    case = receipt_projection_case(amount=100)
    receipt = type(case.receipt)(
        draft_id=case.receipt.draft_id,
        winner_receipt_ids=case.receipt.winner_receipt_ids,
        barrier_snapshot=case.receipt.barrier_snapshot,
        public_row_id=case.receipt.public_row_id,
        projection_id=case.receipt.projection_id,
        authorized_fields=case.receipt.authorized_fields,
        citations=None,
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="citations"):
        build_receipt_envelope_set(receipt, ())


def test_build_receipt_envelope_set_fails_when_cited_material_is_missing():
    case = receipt_projection_case(amount=100)
    materials = tuple(
        material
        for material in _materials_for_receipt(
            case.receipt,
            committed_values=case.source_values,
        )
        if material.artifact_id != "decision-1"
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="missing artifact"):
        build_receipt_envelope_set(case.receipt, materials)


def test_build_receipt_envelope_set_fails_when_required_kind_mismatches():
    case = receipt_projection_case(amount=100)
    materials = tuple(
        ArtifactMaterial(
            artifact_id=material.artifact_id,
            artifact_kind="commit_package",
            schema_version=material.schema_version,
            body=material.body,
        )
        if material.artifact_id == "decision-1"
        else material
        for material in _materials_for_receipt(
            case.receipt,
            committed_values=case.source_values,
        )
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="artifact kind"):
        build_receipt_envelope_set(case.receipt, materials)


def test_build_receipt_envelope_set_fails_on_duplicate_conflicting_material():
    case = receipt_projection_case(amount=100)
    materials = list(
        _materials_for_receipt(case.receipt, committed_values=case.source_values)
    )
    materials.append(
        ArtifactMaterial(
            artifact_id="decision-1",
            artifact_kind="governance_decision",
            schema_version="v1",
            body={"decision_id": "decision-1", "status": "changed"},
        )
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="conflicting material"):
        build_receipt_envelope_set(case.receipt, materials)


def test_build_receipt_envelope_set_requires_committed_value_source_body():
    case = receipt_projection_case(amount=100)
    materials = tuple(
        ArtifactMaterial(
            artifact_id=material.artifact_id,
            artifact_kind=material.artifact_kind,
            schema_version=material.schema_version,
            body={"claim_id": material.artifact_id, "field": "amount"},
        )
        if material.artifact_id == "checked_claim:amount:span-amount"
        else material
        for material in _materials_for_receipt(
            case.receipt,
            committed_values=case.source_values,
        )
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="committed value"):
        build_receipt_envelope_set(case.receipt, materials)


def test_build_receipt_envelope_set_checks_dependency_fingerprint_body():
    case = receipt_projection_case(amount=100)
    materials = tuple(
        ArtifactMaterial(
            artifact_id=material.artifact_id,
            artifact_kind=material.artifact_kind,
            schema_version=material.schema_version,
            body={**material.body, "fingerprint": "sha256:wrong"},
        )
        if material.artifact_id == "fixture-factor"
        else material
        for material in _materials_for_receipt(
            case.receipt,
            committed_values=case.source_values,
        )
    )

    with pytest.raises(ReceiptEnvelopeSetBuildError, match="dependency fingerprint"):
        build_receipt_envelope_set(case.receipt, materials)
