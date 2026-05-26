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

SelectionStatus = Literal["selected", "proposed", "held", "rejected"]

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

SELECTION_STATUSES = frozenset(("selected", "proposed", "held", "rejected"))

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


@dataclass(frozen=True, slots=True)
class ScopedGrant:
    grant_id: str
    subject_id: str
    scope: PipelineScope
    basis: str
    conditions: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    retention: str = "decision_audit"

    def __post_init__(self) -> None:
        _require_non_empty("grant_id", self.grant_id)
        _require_non_empty("subject_id", self.subject_id)
        _require_non_empty("basis", self.basis)
        if self.scope not in PIPELINE_SCOPES:
            raise ValueError(f"unknown pipeline scope: {self.scope}")
        object.__setattr__(self, "conditions", tuple(self.conditions))

    @property
    def authorizes_public_projection(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    decision_id: str
    subject_id: str
    status: SelectionStatus
    basis: str
    target_id: str | None = None
    grants: tuple[ScopedGrant, ...] = field(default_factory=tuple)
    denied_scopes: tuple[PipelineScope, ...] = field(default_factory=tuple)
    retention: str = "decision_audit"

    def __post_init__(self) -> None:
        _require_non_empty("decision_id", self.decision_id)
        _require_non_empty("subject_id", self.subject_id)
        _require_non_empty("basis", self.basis)
        if self.status not in SELECTION_STATUSES:
            raise ValueError(f"unknown selection status: {self.status}")
        for scope in self.denied_scopes:
            if scope not in PIPELINE_SCOPES:
                raise ValueError(f"unknown pipeline scope: {scope}")
        object.__setattr__(self, "grants", tuple(self.grants))
        object.__setattr__(self, "denied_scopes", tuple(self.denied_scopes))

    def allows_scope(self, scope: PipelineScope) -> bool:
        if scope not in PIPELINE_SCOPES:
            raise ValueError(f"unknown pipeline scope: {scope}")
        if scope in self.denied_scopes:
            return False
        return any(grant.scope == scope for grant in self.grants)

    @property
    def authorizes_public_projection(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DecisionLedger:
    ledger_id: str
    policy_profile_id: str
    descriptors: tuple[MaterialDescriptor, ...] = field(default_factory=tuple)
    effects: tuple[PolicyEffect, ...] = field(default_factory=tuple)
    decisions: tuple[SelectionDecision, ...] = field(default_factory=tuple)
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("ledger_id", self.ledger_id)
        _require_non_empty("policy_profile_id", self.policy_profile_id)
        object.__setattr__(self, "descriptors", tuple(self.descriptors))
        object.__setattr__(self, "effects", tuple(self.effects))
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "meta", tuple(self.meta))

    def decision_for(self, decision_id: str) -> SelectionDecision | None:
        return next(
            (
                decision
                for decision in self.decisions
                if decision.decision_id == decision_id
            ),
            None,
        )

    def grants_for(
        self,
        subject_id: str,
        *,
        scope: PipelineScope | None = None,
    ) -> tuple[ScopedGrant, ...]:
        if scope is not None and scope not in PIPELINE_SCOPES:
            raise ValueError(f"unknown pipeline scope: {scope}")
        grants = tuple(
            grant
            for decision in self.decisions
            for grant in decision.grants
            if grant.subject_id == subject_id
        )
        if scope is None:
            return grants
        return tuple(grant for grant in grants if grant.scope == scope)

    def selected_validation_decision_ids(self) -> tuple[str, ...]:
        return tuple(
            decision.decision_id
            for decision in self.decisions
            if decision.status == "selected"
            and decision.allows_scope("validation_handoff")
        )

    @property
    def authorizes_public_projection(self) -> bool:
        return False


def _require_non_empty(field_name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")


__all__ = [
    "PIPELINE_SCOPES",
    "POLICY_EFFECT_KINDS",
    "SELECTION_STATUSES",
    "DecisionLedger",
    "MaterialDescriptor",
    "PipelineScope",
    "PolicyEffect",
    "PolicyEffectKind",
    "ScopedGrant",
    "SelectionDecision",
    "SelectionStatus",
]
