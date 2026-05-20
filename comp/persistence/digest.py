from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any


def artifact_digest(
    *,
    artifact_kind: str,
    schema_version: str,
    body: Mapping[str, Any],
) -> str:
    _require_non_empty("artifact_kind", artifact_kind)
    _require_non_empty("schema_version", schema_version)
    canonical = json.dumps(
        {
            "artifact_kind": artifact_kind,
            "schema_version": schema_version,
            "body": _canonical_value(body),
        },
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _canonical_value(value: Any) -> Any:
    if value is None:
        return {"type": "none", "value": None}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": str(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Artifact digest requires a finite float.")
        return {"type": "float", "value": repr(value)}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Artifact digest requires a finite decimal.")
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, Mapping):
        return {
            "type": "mapping",
            "value": tuple(
                (key, _canonical_value(item))
                for key, item in sorted(
                    _string_key_items(value),
                    key=lambda pair: pair[0],
                )
            ),
        }
    if isinstance(value, tuple):
        return {
            "type": "tuple",
            "value": tuple(_canonical_value(item) for item in value),
        }
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {
            "type": "sequence",
            "value": tuple(_canonical_value(item) for item in value),
        }
    raise TypeError(f"Unsupported artifact digest value: {type(value).__name__}")


def _string_key_items(value: Mapping[Any, Any]) -> tuple[tuple[str, Any], ...]:
    items: list[tuple[str, Any]] = []
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("Artifact digest mappings require string keys.")
        items.append((key, item))
    return tuple(items)


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


__all__ = ["artifact_digest"]
