from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from comp.judgment import (
    CommitReceipt,
    ProjectionBlocked,
    ProjectionSpec,
    project_public_row,
)
from comp.persistence.digest import artifact_digest
from comp.persistence.envelope import ArtifactEnvelope


class PersistenceError(RuntimeError):
    """Base error for persistence boundary violations."""


class ArtifactIntegrityError(PersistenceError):
    """Raised when an artifact envelope digest does not match its body."""


class ArtifactConflict(PersistenceError):
    """Raised when an artifact id is recorded with conflicting content."""


class ReceiptConflict(PersistenceError):
    """Raised when a ledger receipt root is recorded with conflicting content."""


class ProjectionReplayBlocked(PersistenceError):
    """Raised when a materialized projection cannot be replayed from a receipt."""


@runtime_checkable
class ArtifactStore(Protocol):
    """Read boundary for replayable artifact envelopes."""

    def get(self, artifact_id: str) -> ArtifactEnvelope:
        ...


@dataclass(frozen=True, slots=True)
class ReceiptLedgerKey:
    public_row_id: str
    projection_id: str
    draft_id: str

    def __post_init__(self) -> None:
        _require_non_empty("public_row_id", self.public_row_id)
        _require_non_empty("projection_id", self.projection_id)
        _require_non_empty("draft_id", self.draft_id)

    @classmethod
    def from_receipt(cls, receipt: CommitReceipt) -> "ReceiptLedgerKey":
        return cls(
            public_row_id=receipt.public_row_id,
            projection_id=receipt.projection_id,
            draft_id=receipt.draft_id,
        )


@dataclass
class InMemoryArtifactStore:
    _envelopes: dict[str, ArtifactEnvelope] = field(default_factory=dict)

    def record(self, envelope: ArtifactEnvelope) -> ArtifactEnvelope:
        verify_artifact_envelope(envelope)
        existing = self._envelopes.get(envelope.artifact_id)
        if existing is None:
            self._envelopes[envelope.artifact_id] = envelope
            return envelope
        if (
            existing.artifact_kind != envelope.artifact_kind
            or existing.schema_version != envelope.schema_version
            or existing.body_digest != envelope.body_digest
        ):
            raise ArtifactConflict(
                f"Artifact already recorded with different content: "
                f"{envelope.artifact_id}."
            )
        return existing

    def get(self, artifact_id: str) -> ArtifactEnvelope:
        return self._envelopes[artifact_id]

    def envelopes(self) -> tuple[ArtifactEnvelope, ...]:
        return tuple(self._envelopes.values())


@dataclass
class InMemoryReceiptLedger:
    _receipts: dict[ReceiptLedgerKey, CommitReceipt] = field(default_factory=dict)

    def record(self, receipt: CommitReceipt) -> CommitReceipt:
        key = ReceiptLedgerKey.from_receipt(receipt)
        existing = self._receipts.get(key)
        if existing is None:
            self._receipts[key] = receipt
            return receipt
        if existing != receipt:
            raise ReceiptConflict(
                f"CommitReceipt ledger root already recorded with different "
                f"content: {key.public_row_id}."
            )
        return existing

    def get(
        self,
        *,
        public_row_id: str,
        projection_id: str,
        draft_id: str,
    ) -> CommitReceipt:
        return self._receipts[
            ReceiptLedgerKey(
                public_row_id=public_row_id,
                projection_id=projection_id,
                draft_id=draft_id,
            )
        ]

    def receipts(self) -> tuple[CommitReceipt, ...]:
        return tuple(self._receipts.values())


def verify_materialized_public_projection(
    row: Mapping[str, Any],
    projection: ProjectionSpec,
    *,
    receipt: CommitReceipt,
) -> dict[str, Any]:
    try:
        authorized_row = project_public_row(row, projection, receipt=receipt)
    except ProjectionBlocked as exc:
        raise ProjectionReplayBlocked(
            "Materialized public projection cannot be replayed from receipt."
        ) from exc
    if dict(row) != authorized_row:
        raise ProjectionReplayBlocked(
            "Materialized public projection is not the receipt-authorized view."
        )
    return authorized_row


def verify_artifact_envelope(envelope: ArtifactEnvelope) -> None:
    expected_digest = artifact_digest(
        artifact_kind=envelope.artifact_kind,
        schema_version=envelope.schema_version,
        body=envelope.body,
    )
    if envelope.body_digest != expected_digest:
        raise ArtifactIntegrityError(
            f"Artifact body digest mismatch: {envelope.artifact_id}."
        )


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = [
    "PersistenceError",
    "ArtifactIntegrityError",
    "ArtifactConflict",
    "ArtifactStore",
    "ReceiptConflict",
    "ProjectionReplayBlocked",
    "ReceiptLedgerKey",
    "InMemoryArtifactStore",
    "InMemoryReceiptLedger",
    "verify_materialized_public_projection",
    "verify_artifact_envelope",
]
