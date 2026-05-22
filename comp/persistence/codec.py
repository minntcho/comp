from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from comp.judgment.receipts import (
    DependencyFingerprint,
    PublicOutputValueCommitment,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
)


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


def commit_receipt_to_body(receipt: PublicOutputReceipt) -> dict[str, Any]:
    citations = None
    if receipt.citations is not None:
        citations = {
            "governance_decision_id": receipt.citations.governance_decision_id,
            "governance_status": receipt.citations.governance_status,
            "governance_reasons": receipt.citations.governance_reasons,
            "commit_package_id": receipt.citations.commit_package_id,
            "commit_package_complete": receipt.citations.commit_package_complete,
            "subject_id": receipt.citations.subject_id,
            "projection_id": receipt.citations.projection_id,
            "authorized_fields": receipt.citations.authorized_fields,
            "profile_id": receipt.citations.profile_id,
            "report_status": receipt.citations.report_status,
            "checked_claim_fields": receipt.citations.checked_claim_fields,
            "checked_claim_witness_ids": receipt.citations.checked_claim_witness_ids,
            "semantic_judgment_ids": receipt.citations.semantic_judgment_ids,
            "reference_binding_ids": receipt.citations.reference_binding_ids,
            "derived_claim_fields": receipt.citations.derived_claim_fields,
            "derived_claim_ids": receipt.citations.derived_claim_ids,
            "calculation_trace_ids": receipt.citations.calculation_trace_ids,
            "formula_ids": receipt.citations.formula_ids,
            "resolved_obligation_ids": receipt.citations.resolved_obligation_ids,
            "open_obligation_ids": receipt.citations.open_obligation_ids,
            "hazard_ids": receipt.citations.hazard_ids,
            "projection_value_commitments": tuple(
                _projection_value_commitment_to_body(item)
                for item in receipt.citations.projection_value_commitments
            ),
            "dependency_fingerprints": tuple(
                _dependency_fingerprint_to_body(item)
                for item in receipt.citations.dependency_fingerprints
            ),
        }
    return {
        "draft_id": receipt.draft_id,
        "winner_receipt_ids": receipt.winner_receipt_ids,
        "barrier_snapshot": _receipt_value_to_body(receipt.barrier_snapshot),
        "public_row_id": receipt.public_row_id,
        "projection_id": receipt.projection_id,
        "authorized_fields": receipt.authorized_fields,
        "citations": citations,
    }


def commit_receipt_from_body(body: Mapping[str, Any]) -> PublicOutputReceipt:
    citations_body = body["citations"]
    citations = None
    if citations_body is not None:
        citations = PublicOutputReceiptCitations(
            governance_decision_id=citations_body["governance_decision_id"],
            governance_status=citations_body["governance_status"],
            governance_reasons=tuple(citations_body["governance_reasons"]),
            commit_package_id=citations_body["commit_package_id"],
            commit_package_complete=citations_body["commit_package_complete"],
            subject_id=citations_body["subject_id"],
            projection_id=citations_body["projection_id"],
            authorized_fields=tuple(citations_body["authorized_fields"]),
            profile_id=citations_body["profile_id"],
            report_status=citations_body["report_status"],
            checked_claim_fields=tuple(citations_body["checked_claim_fields"]),
            checked_claim_witness_ids=tuple(
                citations_body["checked_claim_witness_ids"]
            ),
            semantic_judgment_ids=tuple(citations_body["semantic_judgment_ids"]),
            reference_binding_ids=tuple(citations_body["reference_binding_ids"]),
            derived_claim_fields=tuple(citations_body["derived_claim_fields"]),
            derived_claim_ids=tuple(citations_body["derived_claim_ids"]),
            calculation_trace_ids=tuple(citations_body["calculation_trace_ids"]),
            formula_ids=tuple(citations_body["formula_ids"]),
            resolved_obligation_ids=tuple(citations_body["resolved_obligation_ids"]),
            open_obligation_ids=tuple(citations_body["open_obligation_ids"]),
            hazard_ids=tuple(citations_body["hazard_ids"]),
            projection_value_commitments=tuple(
                _projection_value_commitment_from_body(item)
                for item in citations_body["projection_value_commitments"]
            ),
            dependency_fingerprints=tuple(
                _dependency_fingerprint_from_body(item)
                for item in citations_body["dependency_fingerprints"]
            ),
        )
    return PublicOutputReceipt(
        draft_id=body["draft_id"],
        winner_receipt_ids=tuple(body["winner_receipt_ids"]),
        barrier_snapshot=_receipt_value_from_body(body["barrier_snapshot"]),
        public_row_id=body["public_row_id"],
        projection_id=body["projection_id"],
        authorized_fields=tuple(body["authorized_fields"]),
        citations=citations,
    )


def _projection_value_commitment_to_body(
    commitment: PublicOutputValueCommitment,
) -> dict[str, Any]:
    return {
        "field": commitment.field,
        "source_kind": commitment.source_kind,
        "source_id": commitment.source_id,
        "value_digest": commitment.value_digest,
        "digest_alg": commitment.digest_alg,
    }


def _projection_value_commitment_from_body(
    body: Mapping[str, Any],
) -> PublicOutputValueCommitment:
    return PublicOutputValueCommitment(
        field=body["field"],
        source_kind=body["source_kind"],
        source_id=body["source_id"],
        value_digest=body["value_digest"],
        digest_alg=body["digest_alg"],
    )


def _dependency_fingerprint_to_body(
    fingerprint: DependencyFingerprint,
) -> dict[str, Any]:
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _dependency_fingerprint_from_body(
    body: Mapping[str, Any],
) -> DependencyFingerprint:
    return DependencyFingerprint(
        dependency_kind=body["dependency_kind"],
        dependency_id=body["dependency_id"],
        fingerprint=body["fingerprint"],
        digest_alg=body["digest_alg"],
    )


def _receipt_value_to_body(value: Any) -> Any:
    if isinstance(value, PublicOutputValueCommitment):
        return {
            "__receipt_type__": "projection_value_commitment",
            "value": _projection_value_commitment_to_body(value),
        }
    if isinstance(value, DependencyFingerprint):
        return {
            "__receipt_type__": "dependency_fingerprint",
            "value": _dependency_fingerprint_to_body(value),
        }
    if isinstance(value, Mapping):
        return {
            str(key): _receipt_value_to_body(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple):
        return tuple(_receipt_value_to_body(item) for item in value)
    if isinstance(value, list):
        return [_receipt_value_to_body(item) for item in value]
    return value


def _receipt_value_from_body(value: Any) -> Any:
    if isinstance(value, Mapping):
        receipt_type = value.get("__receipt_type__")
        if receipt_type == "projection_value_commitment":
            return _projection_value_commitment_from_body(value["value"])
        if receipt_type == "dependency_fingerprint":
            return _dependency_fingerprint_from_body(value["value"])
        return {key: _receipt_value_from_body(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_receipt_value_from_body(item) for item in value)
    if isinstance(value, list):
        return [_receipt_value_from_body(item) for item in value]
    return value


def _string_key_items(value: Mapping[Any, Any]) -> tuple[tuple[str, Any], ...]:
    items: list[tuple[str, Any]] = []
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("Persistence JSON mappings require string keys.")
        items.append((key, item))
    return tuple(items)


__all__ = [
    "commit_receipt_from_body",
    "commit_receipt_to_body",
    "decode_persistence_json",
    "encode_persistence_json",
]
