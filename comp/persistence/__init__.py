"""Persistence boundary primitives for replayable artifact records."""

from comp.persistence.digest import artifact_digest
from comp.persistence.envelope import ArtifactEnvelope
from comp.persistence.ledger import (
    ArtifactConflict,
    ArtifactIntegrityError,
    InMemoryArtifactStore,
    InMemoryReceiptLedger,
    PersistenceError,
    ProjectionReplayBlocked,
    ReceiptConflict,
    ReceiptLedgerKey,
    verify_artifact_envelope,
    verify_materialized_public_projection,
)
from comp.persistence.replay import (
    ArtifactRef,
    ProjectionReplayReport,
    receipt_artifact_refs,
    replay_public_projection,
)

__all__ = [
    "ArtifactConflict",
    "ArtifactEnvelope",
    "ArtifactRef",
    "ArtifactIntegrityError",
    "InMemoryArtifactStore",
    "InMemoryReceiptLedger",
    "PersistenceError",
    "ProjectionReplayBlocked",
    "ProjectionReplayReport",
    "ReceiptConflict",
    "ReceiptLedgerKey",
    "artifact_digest",
    "receipt_artifact_refs",
    "replay_public_projection",
    "verify_artifact_envelope",
    "verify_materialized_public_projection",
]
