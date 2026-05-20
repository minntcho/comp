from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from comp.persistence.digest import artifact_digest


@dataclass(frozen=True)
class ArtifactEnvelope:
    artifact_id: str
    artifact_kind: str
    schema_version: str
    body_digest: str
    body: Mapping[str, Any]
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("artifact_id", self.artifact_id)
        _require_non_empty("artifact_kind", self.artifact_kind)
        _require_non_empty("schema_version", self.schema_version)

    @classmethod
    def from_body(
        cls,
        *,
        artifact_id: str,
        artifact_kind: str,
        schema_version: str,
        body: Mapping[str, Any],
        source_refs: tuple[str, ...] = (),
        meta: tuple[tuple[str, Any], ...] = (),
    ) -> "ArtifactEnvelope":
        return cls(
            artifact_id=artifact_id,
            artifact_kind=artifact_kind,
            schema_version=schema_version,
            body_digest=artifact_digest(
                artifact_kind=artifact_kind,
                schema_version=schema_version,
                body=body,
            ),
            body=body,
            source_refs=tuple(source_refs),
            meta=tuple(meta),
        )


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = ["ArtifactEnvelope"]
