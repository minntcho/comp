from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from comp.judgment.receipts import (
    DependencyFingerprint,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputValueCommitment,
)


class ReceiptAuthenticityError(RuntimeError):
    """Base error for receipt authenticity verification."""


class UnknownReceiptIssuer(ReceiptAuthenticityError):
    """Raised by a key registry when it cannot resolve an issuer/key pair."""

    def __init__(self, issuer_id: str, key_id: str):
        super().__init__(f"Unknown receipt issuer/key: {issuer_id}/{key_id}.")
        self.issuer_id = issuer_id
        self.key_id = key_id


class UnsupportedReceiptSignatureAlgorithm(ReceiptAuthenticityError):
    """Raised by a key registry when a signature algorithm is unsupported."""


class MalformedReceiptSignature(ReceiptAuthenticityError):
    """Raised by a key registry when a signature payload is malformed."""


class ReceiptKeyRegistry(Protocol):
    """Verification boundary for receipt signatures.

    Implementations may use real cryptography later. The trust kernel only
    requires this narrow method so receipt authenticity does not become replay
    or projection authority.
    """

    def verify_signature(
        self,
        signature: "ReceiptSignature",
        *,
        signed_body_digest: str,
    ) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class ReceiptIssuer:
    issuer_id: str
    key_id: str
    algorithm: str

    def __post_init__(self) -> None:
        _require_non_empty("issuer_id", self.issuer_id)
        _require_non_empty("key_id", self.key_id)
        _require_non_empty("algorithm", self.algorithm)


@dataclass(frozen=True, slots=True)
class ReceiptSignature:
    issuer_id: str
    key_id: str
    algorithm: str
    signed_body_digest: str
    signature: str

    def __post_init__(self) -> None:
        _require_non_empty("issuer_id", self.issuer_id)
        _require_non_empty("key_id", self.key_id)
        _require_non_empty("algorithm", self.algorithm)
        _require_non_empty("signed_body_digest", self.signed_body_digest)
        _require_non_empty("signature", self.signature)


@dataclass(frozen=True, slots=True)
class SignedPublicOutputReceipt:
    receipt: PublicOutputReceipt
    signature: ReceiptSignature


@dataclass(frozen=True, slots=True)
class ReceiptVerificationResult:
    status: str
    issuer_id: str | None
    key_id: str | None
    signed_body_digest: str
    errors: tuple[str, ...] = field(default_factory=tuple)


def verify_public_output_receipt(
    receipt: PublicOutputReceipt | SignedPublicOutputReceipt,
    key_registry: ReceiptKeyRegistry,
) -> ReceiptVerificationResult:
    public_receipt = _public_receipt(receipt)
    actual_digest = public_output_receipt_signed_body_digest(public_receipt)

    if isinstance(receipt, PublicOutputReceipt):
        return ReceiptVerificationResult(
            status="unsigned_legacy",
            issuer_id=None,
            key_id=None,
            signed_body_digest=actual_digest,
        )

    signature = receipt.signature
    if signature.signed_body_digest != actual_digest:
        return ReceiptVerificationResult(
            status="invalid_signature",
            issuer_id=signature.issuer_id,
            key_id=signature.key_id,
            signed_body_digest=actual_digest,
            errors=("Receipt body digest does not match signature.",),
        )

    try:
        valid = key_registry.verify_signature(
            signature,
            signed_body_digest=actual_digest,
        )
    except UnknownReceiptIssuer as exc:
        return _failed_verification(
            "unknown_issuer",
            signature,
            actual_digest,
            exc,
        )
    except UnsupportedReceiptSignatureAlgorithm as exc:
        return _failed_verification(
            "unsupported_algorithm",
            signature,
            actual_digest,
            exc,
        )
    except MalformedReceiptSignature as exc:
        return _failed_verification(
            "malformed_signature",
            signature,
            actual_digest,
            exc,
        )

    if not valid:
        return ReceiptVerificationResult(
            status="invalid_signature",
            issuer_id=signature.issuer_id,
            key_id=signature.key_id,
            signed_body_digest=actual_digest,
            errors=("Receipt signature verification failed.",),
        )
    return ReceiptVerificationResult(
        status="verified",
        issuer_id=signature.issuer_id,
        key_id=signature.key_id,
        signed_body_digest=actual_digest,
    )


def public_output_receipt_signed_body(receipt: PublicOutputReceipt) -> dict[str, Any]:
    return {
        "schema_version": "public-output-receipt-signature-v1",
        "draft_id": receipt.draft_id,
        "winner_receipt_ids": list(receipt.winner_receipt_ids),
        "barrier_snapshot": _receipt_value_to_body(receipt.barrier_snapshot),
        "public_row_id": receipt.public_row_id,
        "projection_id": receipt.projection_id,
        "authorized_fields": list(receipt.authorized_fields),
        "citations": _citations_to_body(receipt.citations),
    }


def public_output_receipt_signed_body_digest(receipt: PublicOutputReceipt) -> str:
    canonical = json.dumps(
        public_output_receipt_signed_body(receipt),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _public_receipt(
    receipt: PublicOutputReceipt | SignedPublicOutputReceipt,
) -> PublicOutputReceipt:
    if isinstance(receipt, SignedPublicOutputReceipt):
        return receipt.receipt
    return receipt


def _failed_verification(
    status: str,
    signature: ReceiptSignature,
    signed_body_digest: str,
    exc: ReceiptAuthenticityError,
) -> ReceiptVerificationResult:
    return ReceiptVerificationResult(
        status=status,
        issuer_id=signature.issuer_id,
        key_id=signature.key_id,
        signed_body_digest=signed_body_digest,
        errors=(str(exc),),
    )


def _citations_to_body(
    citations: PublicOutputReceiptCitations | None,
) -> dict[str, Any] | None:
    if citations is None:
        return None
    return {
        "governance_decision_id": citations.governance_decision_id,
        "governance_status": citations.governance_status,
        "governance_reasons": list(citations.governance_reasons),
        "commit_package_id": citations.commit_package_id,
        "commit_package_complete": citations.commit_package_complete,
        "subject_id": citations.subject_id,
        "projection_id": citations.projection_id,
        "authorized_fields": list(citations.authorized_fields),
        "profile_id": citations.profile_id,
        "report_status": citations.report_status,
        "checked_claim_fields": list(citations.checked_claim_fields),
        "checked_claim_witness_ids": list(citations.checked_claim_witness_ids),
        "semantic_judgment_ids": list(citations.semantic_judgment_ids),
        "reference_binding_ids": list(citations.reference_binding_ids),
        "derived_claim_fields": list(citations.derived_claim_fields),
        "derived_claim_ids": list(citations.derived_claim_ids),
        "calculation_trace_ids": list(citations.calculation_trace_ids),
        "formula_ids": list(citations.formula_ids),
        "resolved_obligation_ids": list(citations.resolved_obligation_ids),
        "open_obligation_ids": list(citations.open_obligation_ids),
        "hazard_ids": list(citations.hazard_ids),
        "projection_value_commitments": [
            _value_commitment_to_body(commitment)
            for commitment in citations.projection_value_commitments
        ],
        "dependency_fingerprints": [
            _dependency_fingerprint_to_body(fingerprint)
            for fingerprint in citations.dependency_fingerprints
        ],
    }


def _value_commitment_to_body(
    commitment: PublicOutputValueCommitment,
) -> dict[str, str]:
    return {
        "field": commitment.field,
        "source_kind": commitment.source_kind,
        "source_id": commitment.source_id,
        "value_digest": commitment.value_digest,
        "digest_alg": commitment.digest_alg,
    }


def _dependency_fingerprint_to_body(
    fingerprint: DependencyFingerprint,
) -> dict[str, str]:
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _receipt_value_to_body(value: Any) -> Any:
    if isinstance(value, PublicOutputValueCommitment):
        return {
            "__receipt_type__": "projection_value_commitment",
            "value": _value_commitment_to_body(value),
        }
    if isinstance(value, DependencyFingerprint):
        return {
            "__receipt_type__": "dependency_fingerprint",
            "value": _dependency_fingerprint_to_body(value),
        }
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Receipt signed body requires a finite float.")
        return {"__receipt_type__": "float", "value": repr(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Receipt signed body requires a finite decimal.")
        return {"__receipt_type__": "decimal", "value": str(value)}
    if isinstance(value, Mapping):
        return {
            str(key): _receipt_value_to_body(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [_receipt_value_to_body(item) for item in value]
    raise TypeError(f"Unsupported receipt signed body value: {type(value).__name__}")


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = [
    "ReceiptAuthenticityError",
    "UnknownReceiptIssuer",
    "UnsupportedReceiptSignatureAlgorithm",
    "MalformedReceiptSignature",
    "ReceiptKeyRegistry",
    "ReceiptIssuer",
    "ReceiptSignature",
    "SignedPublicOutputReceipt",
    "ReceiptVerificationResult",
    "public_output_receipt_signed_body",
    "public_output_receipt_signed_body_digest",
    "verify_public_output_receipt",
]
