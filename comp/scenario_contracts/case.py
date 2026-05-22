from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from comp.judgment import PublicOutputReceipt, PublicOutputSpec
from comp.persistence.ledger import ReceiptLedgerKey
from comp.persistence.mysql import commit_receipt_from_body
from comp.scenario_contracts.manifest import ScenarioManifestError


@dataclass(frozen=True, slots=True)
class RuntimeProjection:
    public_row_id: str
    projection_id: str
    draft_id: str
    output_fields: tuple[str, ...]
    row: Mapping[str, Any]

    @property
    def receipt_key(self) -> ReceiptLedgerKey:
        return ReceiptLedgerKey(
            public_row_id=self.public_row_id,
            projection_id=self.projection_id,
            draft_id=self.draft_id,
        )

    @property
    def projection_spec(self) -> PublicOutputSpec:
        return PublicOutputSpec(self.projection_id, self.output_fields)


@dataclass(frozen=True, slots=True)
class RuntimeCase:
    case_id: str
    receipts: tuple[PublicOutputReceipt, ...]
    projections: tuple[RuntimeProjection, ...]


def load_runtime_case(path: str | Path) -> RuntimeCase:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ScenarioManifestError("RuntimeCase file must contain an object.")
    return runtime_case_from_mapping(payload)


def runtime_case_from_mapping(payload: Mapping[str, Any]) -> RuntimeCase:
    case_id = _required_str(payload, "case_id")
    receipts = payload.get("receipts")
    projections = payload.get("projections")
    if not isinstance(receipts, list):
        raise ScenarioManifestError("RuntimeCase.receipts must be a list.")
    if not isinstance(projections, list):
        raise ScenarioManifestError("RuntimeCase.projections must be a list.")
    return RuntimeCase(
        case_id=case_id,
        receipts=tuple(
            commit_receipt_from_body(_required_mapping(item, "receipt"))
            for item in receipts
        ),
        projections=tuple(
            _projection_from_mapping(_required_mapping(item, "projection"))
            for item in projections
        ),
    )


def _projection_from_mapping(payload: Mapping[str, Any]) -> RuntimeProjection:
    output_fields = payload.get("output_fields")
    row = payload.get("row")
    if not isinstance(output_fields, list) or not all(
        isinstance(field, str) for field in output_fields
    ):
        raise ScenarioManifestError("RuntimeProjection.output_fields must be strings.")
    if not isinstance(row, Mapping):
        raise ScenarioManifestError("RuntimeProjection.row must be an object.")
    return RuntimeProjection(
        public_row_id=_required_str(payload, "public_row_id"),
        projection_id=_required_str(payload, "projection_id"),
        draft_id=_required_str(payload, "draft_id"),
        output_fields=tuple(output_fields),
        row=dict(row),
    )


def _required_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ScenarioManifestError(f"{label} must be an object.")
    return value


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ScenarioManifestError(f"{key} must be a non-empty string.")
    return value


__all__ = [
    "RuntimeCase",
    "RuntimeProjection",
    "load_runtime_case",
    "runtime_case_from_mapping",
]
