from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

PolicyEffectKind = Literal[
    "select",
    "propose",
    "hold",
    "reject",
    "escalate",
    "request_evidence",
    "grant_scope",
    "restrict_scope",
    "require_review",
    "require_replay_material",
    "set_retention",
]

PipelineScope = Literal[
    "candidate_generation",
    "selection_evaluation",
    "validation_context",
    "validation_handoff",
    "projection_candidate",
    "replay_support",
    "audit_only",
]

POLICY_EFFECT_KINDS = frozenset(
    (
        "select",
        "propose",
        "hold",
        "reject",
        "escalate",
        "request_evidence",
        "grant_scope",
        "restrict_scope",
        "require_review",
        "require_replay_material",
        "set_retention",
    )
)

PIPELINE_SCOPES = frozenset(
    (
        "candidate_generation",
        "selection_evaluation",
        "validation_context",
        "validation_handoff",
        "projection_candidate",
        "replay_support",
        "audit_only",
    )
)

_SCOPED_EFFECT_KINDS = frozenset(("grant_scope", "restrict_scope"))


@dataclass(frozen=True, slots=True)
class MaterialDescriptor:
    material_id: str
    material_kind: str = "external_material"
    field_knownness: str = "unknown"
    risk_tier: str = "unknown"
    projection_sensitivity: str = "unknown"
    evidence_availability: str = "unknown"
    source_ref: str | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("material_id", self.material_id)
        _require_non_empty("material_kind", self.material_kind)
        object.__setattr__(self, "attributes", tuple(self.attributes))


@dataclass(frozen=True, slots=True)
class PolicyEffect:
    effect_id: str
    effect_kind: PolicyEffectKind
    subject_id: str
    basis: str
    scope: PipelineScope | None = None
    reason: str = ""
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("effect_id", self.effect_id)
        _require_non_empty("subject_id", self.subject_id)
        _require_non_empty("basis", self.basis)
        if self.effect_kind not in POLICY_EFFECT_KINDS:
            raise ValueError(f"unknown policy effect kind: {self.effect_kind}")
        if self.scope is not None and self.scope not in PIPELINE_SCOPES:
            raise ValueError(f"unknown pipeline scope: {self.scope}")
        if self.effect_kind in _SCOPED_EFFECT_KINDS and self.scope is None:
            raise ValueError(f"scope is required for {self.effect_kind}")
        object.__setattr__(self, "payload", tuple(self.payload))


def _require_non_empty(field_name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")


__all__ = [
    "PIPELINE_SCOPES",
    "POLICY_EFFECT_KINDS",
    "MaterialDescriptor",
    "PipelineScope",
    "PolicyEffect",
    "PolicyEffectKind",
]
