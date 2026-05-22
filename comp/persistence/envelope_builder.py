from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from comp.judgment import PublicOutputReceipt
from comp.persistence.envelope import ArtifactEnvelope
from comp.persistence.ledger import PersistenceError
from comp.persistence.replay import ArtifactRef, receipt_artifact_refs


class ReceiptEnvelopeSetBuildError(PersistenceError):
    """Raised when receipt-cited artifact material cannot produce envelopes."""


class ArtifactRecorder(Protocol):
    def record(self, envelope: ArtifactEnvelope) -> ArtifactEnvelope:
        ...


@dataclass(frozen=True)
class ArtifactMaterial:
    artifact_id: str
    artifact_kind: str
    schema_version: str
    body: Mapping[str, Any]
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def to_envelope(self) -> ArtifactEnvelope:
        return ArtifactEnvelope.from_body(
            artifact_id=self.artifact_id,
            artifact_kind=self.artifact_kind,
            schema_version=self.schema_version,
            body=self.body,
            source_refs=tuple(self.source_refs),
            meta=tuple(self.meta),
        )


def build_receipt_envelope_set(
    receipt: PublicOutputReceipt | None,
    materials: Iterable[ArtifactMaterial],
    *,
    record_to: ArtifactRecorder | None = None,
) -> tuple[ArtifactEnvelope, ...]:
    if receipt is None:
        raise ReceiptEnvelopeSetBuildError("Receipt envelope set requires a receipt.")
    if receipt.citations is None:
        raise ReceiptEnvelopeSetBuildError(
            "Receipt envelope set requires receipt citations."
        )

    available = _envelopes_by_id(materials)
    required_refs = receipt_artifact_refs(receipt)
    envelopes: list[ArtifactEnvelope] = []
    for ref in required_refs:
        envelope = _required_envelope(ref, available)
        _verify_value_commitment_source(ref, envelope, receipt)
        _verify_dependency_fingerprint_source(ref, envelope, receipt)
        envelopes.append(envelope)

    if record_to is None:
        return tuple(envelopes)
    return tuple(record_to.record(envelope) for envelope in envelopes)


def _envelopes_by_id(
    materials: Iterable[ArtifactMaterial],
) -> dict[str, ArtifactEnvelope]:
    envelopes: dict[str, ArtifactEnvelope] = {}
    for material in materials:
        envelope = material.to_envelope()
        existing = envelopes.get(envelope.artifact_id)
        if existing is None:
            envelopes[envelope.artifact_id] = envelope
            continue
        if (
            existing.artifact_kind != envelope.artifact_kind
            or existing.schema_version != envelope.schema_version
            or existing.body_digest != envelope.body_digest
        ):
            raise ReceiptEnvelopeSetBuildError(
                f"Receipt envelope set has conflicting material: "
                f"{envelope.artifact_id}."
            )
    return envelopes


def _required_envelope(
    ref: ArtifactRef,
    available: Mapping[str, ArtifactEnvelope],
) -> ArtifactEnvelope:
    try:
        envelope = available[ref.artifact_id]
    except KeyError as exc:
        raise ReceiptEnvelopeSetBuildError(
            f"Receipt envelope set missing artifact: {ref.artifact_id}."
        ) from exc
    if envelope.artifact_kind != ref.artifact_kind:
        raise ReceiptEnvelopeSetBuildError(
            f"Receipt envelope set artifact kind mismatch: {ref.artifact_id}."
        )
    return envelope


def _verify_value_commitment_source(
    ref: ArtifactRef,
    envelope: ArtifactEnvelope,
    receipt: PublicOutputReceipt,
) -> None:
    assert receipt.citations is not None
    source_refs = {
        (commitment.source_id, commitment.source_kind)
        for commitment in receipt.citations.projection_value_commitments
    }
    if (ref.artifact_id, ref.artifact_kind) not in source_refs:
        return
    if "value" not in envelope.body:
        raise ReceiptEnvelopeSetBuildError(
            "Receipt envelope set committed value source lacks value: "
            f"{ref.artifact_id}."
        )


def _verify_dependency_fingerprint_source(
    ref: ArtifactRef,
    envelope: ArtifactEnvelope,
    receipt: PublicOutputReceipt,
) -> None:
    assert receipt.citations is not None
    fingerprints = {
        (fingerprint.dependency_id, fingerprint.dependency_kind): fingerprint
        for fingerprint in receipt.citations.dependency_fingerprints
    }
    fingerprint = fingerprints.get((ref.artifact_id, ref.artifact_kind))
    if fingerprint is None:
        return

    body = envelope.body
    if (
        body.get("dependency_kind") != fingerprint.dependency_kind
        or body.get("dependency_id") != fingerprint.dependency_id
        or body.get("fingerprint") != fingerprint.fingerprint
        or body.get("digest_alg") != fingerprint.digest_alg
    ):
        raise ReceiptEnvelopeSetBuildError(
            "Receipt envelope set dependency fingerprint mismatch: "
            f"{ref.artifact_id}."
        )


__all__ = [
    "ArtifactMaterial",
    "ArtifactRecorder",
    "ReceiptEnvelopeSetBuildError",
    "build_receipt_envelope_set",
]
