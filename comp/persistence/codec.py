from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any


_TYPE_KEY = "__comp_type__"
_VALUE_KEY = "value"


def encode_persistence_json(value: Any) -> Any:
    if value is None:
        return {_TYPE_KEY: "none", _VALUE_KEY: None}
    if isinstance(value, bool):
        return {_TYPE_KEY: "bool", _VALUE_KEY: value}
    if isinstance(value, int):
        return {_TYPE_KEY: "int", _VALUE_KEY: str(value)}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Persistence JSON requires a finite float.")
        return {_TYPE_KEY: "float", _VALUE_KEY: repr(value)}
    if isinstance(value, str):
        return {_TYPE_KEY: "str", _VALUE_KEY: value}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Persistence JSON requires a finite decimal.")
        return {_TYPE_KEY: "decimal", _VALUE_KEY: str(value)}
    if isinstance(value, Mapping):
        return {
            _TYPE_KEY: "mapping",
            _VALUE_KEY: [
                [key, encode_persistence_json(item)]
                for key, item in sorted(
                    _string_key_items(value),
                    key=lambda pair: pair[0],
                )
            ],
        }
    if isinstance(value, tuple):
        return {
            _TYPE_KEY: "tuple",
            _VALUE_KEY: [encode_persistence_json(item) for item in value],
        }
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {
            _TYPE_KEY: "list",
            _VALUE_KEY: [encode_persistence_json(item) for item in value],
        }
    raise TypeError(f"Unsupported persistence JSON value: {type(value).__name__}")


def decode_persistence_json(value: Any) -> Any:
    if not isinstance(value, Mapping) or _TYPE_KEY not in value:
        raise TypeError("Persistence JSON value is missing __comp_type__.")
    kind = value[_TYPE_KEY]
    raw = value[_VALUE_KEY]
    if kind == "none":
        return None
    if kind == "bool":
        return bool(raw)
    if kind == "int":
        return int(raw)
    if kind == "float":
        return float(raw)
    if kind == "str":
        return str(raw)
    if kind == "decimal":
        return Decimal(str(raw))
    if kind == "mapping":
        return {str(key): decode_persistence_json(item) for key, item in raw}
    if kind == "tuple":
        return tuple(decode_persistence_json(item) for item in raw)
    if kind == "list":
        return [decode_persistence_json(item) for item in raw]
    raise TypeError(f"Unsupported persistence JSON type: {kind}")


def _string_key_items(value: Mapping[Any, Any]) -> tuple[tuple[str, Any], ...]:
    items: list[tuple[str, Any]] = []
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("Persistence JSON mappings require string keys.")
        items.append((key, item))
    return tuple(items)


__all__ = ["decode_persistence_json", "encode_persistence_json"]
