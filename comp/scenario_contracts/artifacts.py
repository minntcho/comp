from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from comp.persistence.codec import decode_persistence_json, encode_persistence_json
from comp.persistence.envelope import ArtifactEnvelope
from comp.scenario_contracts.manifest import ScenarioManifestError


def load_artifact_envelopes(path: str | Path) -> tuple[ArtifactEnvelope, ...]:
    envelopes: list[ArtifactEnvelope] = []
    artifact_lines = Path(path).read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(artifact_lines, 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ScenarioManifestError(
                f"artifact_envelopes line {line_number} must be an object."
            )
        envelopes.append(artifact_envelope_from_mapping(payload))
    return tuple(envelopes)


def write_artifact_envelopes(
    envelopes: Iterable[ArtifactEnvelope],
    path: str | Path,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(artifact_envelope_to_mapping(envelope), sort_keys=True)
        for envelope in envelopes
    ]
    artifact_path.write_text("\n".join(lines), encoding="utf-8")
    return artifact_path


def artifact_envelope_to_mapping(envelope: ArtifactEnvelope) -> dict[str, object]:
    return {
        "artifact_id": envelope.artifact_id,
        "artifact_kind": envelope.artifact_kind,
        "schema_version": envelope.schema_version,
        "body_digest": envelope.body_digest,
        "body": encode_persistence_json(envelope.body),
        "source_refs": encode_persistence_json(envelope.source_refs),
        "meta": encode_persistence_json(envelope.meta),
    }


def artifact_envelope_from_mapping(payload: Mapping[str, Any]) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_id=_required_str(payload, "artifact_id"),
        artifact_kind=_required_str(payload, "artifact_kind"),
        schema_version=_required_str(payload, "schema_version"),
        body_digest=_required_str(payload, "body_digest"),
        body=decode_persistence_json(payload["body"]),
        source_refs=_tuple_value(decode_persistence_json(payload["source_refs"])),
        meta=_tuple_pair_value(decode_persistence_json(payload["meta"])),
    )


def _tuple_value(value: Any) -> tuple[str, ...]:
    if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise ScenarioManifestError("ArtifactEnvelope.source_refs must be strings.")


def _tuple_pair_value(value: Any) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, tuple):
        raise ScenarioManifestError("ArtifactEnvelope.meta must be a tuple.")
    pairs: list[tuple[str, Any]] = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
        ):
            raise ScenarioManifestError("ArtifactEnvelope.meta must contain pairs.")
        pairs.append((item[0], item[1]))
    return tuple(pairs)


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ScenarioManifestError(f"{key} must be a non-empty string.")
    return value


__all__ = [
    "artifact_envelope_from_mapping",
    "artifact_envelope_to_mapping",
    "load_artifact_envelopes",
    "write_artifact_envelopes",
]
