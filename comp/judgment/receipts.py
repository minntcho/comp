from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class SelectionReceipt:
    bundle_id: str
    frontier_ids: tuple[str, ...]
    winner_id: str | None
    bundle_version: int
    reason: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ProjectionValueCommitment:
    field: str
    source_kind: str
    source_id: str
    value_digest: str
    digest_alg: str = "sha256"

    @classmethod
    def from_value(
        cls,
        *,
        field: str,
        source_kind: str,
        source_id: str,
        value: Any,
    ) -> "ProjectionValueCommitment":
        return cls(
            field=field,
            source_kind=source_kind,
            source_id=source_id,
            value_digest=_value_digest(value),
        )

    def matches_value(self, value: Any) -> bool:
        return self.value_digest == _value_digest(value)


@dataclass(frozen=True, slots=True)
class DependencyFingerprint:
    dependency_kind: str
    dependency_id: str
    fingerprint: str
    digest_alg: str = "sha256"

    @classmethod
    def from_payload(
        cls,
        *,
        dependency_kind: str,
        dependency_id: str,
        payload: Mapping[str, Any],
    ) -> "DependencyFingerprint":
        return cls(
            dependency_kind=dependency_kind,
            dependency_id=dependency_id,
            fingerprint=_value_digest(payload),
        )


@dataclass(frozen=True, slots=True)
class CommitReceiptCitations:
    governance_decision_id: str
    governance_status: str
    governance_reasons: tuple[str, ...]
    commit_package_id: str
    commit_package_complete: bool
    subject_id: str
    projection_id: str
    authorized_fields: tuple[str, ...]
    profile_id: str | None
    report_status: str
    checked_claim_fields: tuple[str, ...]
    checked_claim_witness_ids: tuple[str, ...]
    semantic_judgment_ids: tuple[str, ...]
    reference_binding_ids: tuple[str, ...]
    derived_claim_fields: tuple[str, ...]
    derived_claim_ids: tuple[str, ...]
    calculation_trace_ids: tuple[str, ...]
    formula_ids: tuple[str, ...]
    resolved_obligation_ids: tuple[str, ...]
    open_obligation_ids: tuple[str, ...]
    hazard_ids: tuple[str, ...]
    projection_value_commitments: tuple[ProjectionValueCommitment, ...] = field(
        default_factory=tuple
    )
    dependency_fingerprints: tuple[DependencyFingerprint, ...] = field(
        default_factory=tuple
    )

    def to_barrier_snapshot(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("governance_decision_id", self.governance_decision_id),
            ("governance_status", self.governance_status),
            ("governance_reasons", self.governance_reasons),
            ("commit_package_id", self.commit_package_id),
            ("commit_package_complete", self.commit_package_complete),
            ("subject_id", self.subject_id),
            ("projection_id", self.projection_id),
            ("authorized_fields", self.authorized_fields),
            ("profile_id", self.profile_id),
            ("report_status", self.report_status),
            ("checked_claim_fields", self.checked_claim_fields),
            ("checked_claim_witness_ids", self.checked_claim_witness_ids),
            ("semantic_judgment_ids", self.semantic_judgment_ids),
            ("reference_binding_ids", self.reference_binding_ids),
            ("derived_claim_fields", self.derived_claim_fields),
            ("derived_claim_ids", self.derived_claim_ids),
            ("calculation_trace_ids", self.calculation_trace_ids),
            ("formula_ids", self.formula_ids),
            ("resolved_obligation_ids", self.resolved_obligation_ids),
            ("open_obligation_ids", self.open_obligation_ids),
            ("hazard_ids", self.hazard_ids),
            (
                "projection_value_commitments",
                self.projection_value_commitments,
            ),
            ("dependency_fingerprints", self.dependency_fingerprints),
        )


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    draft_id: str
    winner_receipt_ids: tuple[str, ...]
    barrier_snapshot: tuple[tuple[str, Any], ...]
    public_row_id: str
    projection_id: str
    authorized_fields: tuple[str, ...]
    citations: CommitReceiptCitations | None = None


def _value_digest(value: Any) -> str:
    canonical = json.dumps(
        _canonical_value(value),
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
            raise ValueError("Projection value commitment requires a finite float.")
        return {"type": "float", "value": repr(value)}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Projection value commitment requires a finite decimal.")
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, Mapping):
        return {
            "type": "mapping",
            "value": tuple(
                (str(key), _canonical_value(item))
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
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
    raise TypeError(
        f"Unsupported projection value for commitment: {type(value).__name__}"
    )


__all__ = [
    "SelectionReceipt",
    "ProjectionValueCommitment",
    "DependencyFingerprint",
    "CommitReceipt",
    "CommitReceiptCitations",
]
