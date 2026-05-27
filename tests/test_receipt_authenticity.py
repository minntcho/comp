from __future__ import annotations

from dataclasses import replace

from comp import (
    MalformedReceiptSignature,
    ReceiptIssuer,
    ReceiptSignature,
    SignedPublicOutputReceipt,
    UnknownReceiptIssuer,
    UnsupportedReceiptSignatureAlgorithm,
    public_output_receipt_signed_body_digest,
    verify_public_output_receipt,
)
from comp.persistence.codec import commit_receipt_from_body, commit_receipt_to_body
from comp.persistence import replay_public_projection
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)


class RecordingKeyRegistry:
    def __init__(
        self,
        *,
        known_issuer: bool = True,
        valid_signature: bool = True,
        unsupported_algorithm: bool = False,
        malformed_signature: bool = False,
    ):
        self.known_issuer = known_issuer
        self.valid_signature = valid_signature
        self.unsupported_algorithm = unsupported_algorithm
        self.malformed_signature = malformed_signature
        self.calls = []

    def verify_signature(self, signature, *, signed_body_digest):
        self.calls.append((signature, signed_body_digest))
        if not self.known_issuer:
            raise UnknownReceiptIssuer(signature.issuer_id, signature.key_id)
        if self.unsupported_algorithm:
            raise UnsupportedReceiptSignatureAlgorithm(
                f"Unsupported receipt signature algorithm: {signature.algorithm}."
            )
        if self.malformed_signature:
            raise MalformedReceiptSignature("Malformed receipt signature.")
        return self.valid_signature


def _signature_for(receipt, *, issuer_id="issuer-1", key_id="key-1"):
    digest = public_output_receipt_signed_body_digest(receipt)
    return ReceiptSignature(
        issuer_id=issuer_id,
        key_id=key_id,
        algorithm="test-signature",
        signed_body_digest=digest,
        signature=f"signature:{digest}",
    )


def test_receipt_issuer_names_the_signing_key_and_algorithm():
    issuer = ReceiptIssuer(
        issuer_id="issuer-1",
        key_id="key-1",
        algorithm="test-signature",
    )

    assert issuer.issuer_id == "issuer-1"
    assert issuer.key_id == "key-1"
    assert issuer.algorithm == "test-signature"


def test_unsigned_legacy_receipt_body_round_trips_without_signature_material():
    case = receipt_projection_case()

    restored = commit_receipt_from_body(commit_receipt_to_body(case.receipt))
    result = verify_public_output_receipt(restored, RecordingKeyRegistry())

    assert restored == case.receipt
    assert result.status == "unsigned_legacy"


def test_unsigned_legacy_receipt_verification_is_not_signature_failure():
    case = receipt_projection_case()
    registry = RecordingKeyRegistry()

    result = verify_public_output_receipt(case.receipt, registry)

    assert result.status == "unsigned_legacy"
    assert result.issuer_id is None
    assert result.key_id is None
    assert result.signed_body_digest == public_output_receipt_signed_body_digest(
        case.receipt
    )
    assert result.errors == ()
    assert registry.calls == []


def test_unsigned_legacy_receipt_remains_replayable_with_valid_artifacts():
    case = receipt_projection_case()
    store = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.public_row,
    )

    authenticity = verify_public_output_receipt(
        case.receipt,
        RecordingKeyRegistry(),
    )
    replay = replay_public_projection(
        case.public_row,
        case.projection,
        receipt=case.receipt,
        artifacts=store,
    )

    assert authenticity.status == "unsigned_legacy"
    assert replay.public_row == case.public_row


def test_signed_receipt_verifies_known_issuer_without_running_replay():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt)
    signed = SignedPublicOutputReceipt(receipt=case.receipt, signature=signature)
    registry = RecordingKeyRegistry()

    result = verify_public_output_receipt(signed, registry)

    assert result.status == "verified"
    assert result.issuer_id == "issuer-1"
    assert result.key_id == "key-1"
    assert result.signed_body_digest == signature.signed_body_digest
    assert result.errors == ()
    assert registry.calls == [(signature, signature.signed_body_digest)]


def test_signed_receipt_reports_unknown_issuer_as_authenticity_status():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt, issuer_id="unknown-issuer")
    signed = SignedPublicOutputReceipt(receipt=case.receipt, signature=signature)

    result = verify_public_output_receipt(
        signed,
        RecordingKeyRegistry(known_issuer=False),
    )

    assert result.status == "unknown_issuer"
    assert result.issuer_id == "unknown-issuer"
    assert result.key_id == "key-1"
    assert result.errors == ("Unknown receipt issuer/key: unknown-issuer/key-1.",)


def test_signed_receipt_reports_invalid_signature_from_key_registry():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt)
    signed = SignedPublicOutputReceipt(receipt=case.receipt, signature=signature)

    result = verify_public_output_receipt(
        signed,
        RecordingKeyRegistry(valid_signature=False),
    )

    assert result.status == "invalid_signature"
    assert result.errors == ("Receipt signature verification failed.",)


def test_signed_receipt_reports_unsupported_algorithm_as_authenticity_status():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt)
    signed = SignedPublicOutputReceipt(receipt=case.receipt, signature=signature)

    result = verify_public_output_receipt(
        signed,
        RecordingKeyRegistry(unsupported_algorithm=True),
    )

    assert result.status == "unsupported_algorithm"
    assert result.errors == (
        "Unsupported receipt signature algorithm: test-signature.",
    )


def test_signed_receipt_reports_malformed_signature_as_authenticity_status():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt)
    signed = SignedPublicOutputReceipt(receipt=case.receipt, signature=signature)

    result = verify_public_output_receipt(
        signed,
        RecordingKeyRegistry(malformed_signature=True),
    )

    assert result.status == "malformed_signature"
    assert result.errors == ("Malformed receipt signature.",)


def test_changed_signed_receipt_body_is_invalid_before_registry_verification():
    case = receipt_projection_case()
    signature = _signature_for(case.receipt)
    changed_receipt = replace(case.receipt, public_row_id="public-row-2")
    signed = SignedPublicOutputReceipt(
        receipt=changed_receipt,
        signature=signature,
    )
    registry = RecordingKeyRegistry()

    result = verify_public_output_receipt(signed, registry)

    assert result.status == "invalid_signature"
    assert result.issuer_id == "issuer-1"
    assert result.key_id == "key-1"
    assert result.signed_body_digest != signature.signed_body_digest
    assert result.errors == ("Receipt body digest does not match signature.",)
    assert registry.calls == []
