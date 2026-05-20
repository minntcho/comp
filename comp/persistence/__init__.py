"""Persistence boundary primitives for replayable artifact records."""

from comp.persistence.digest import artifact_digest
from comp.persistence.envelope import ArtifactEnvelope

__all__ = [
    "ArtifactEnvelope",
    "artifact_digest",
]
