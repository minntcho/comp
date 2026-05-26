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
_VALIDATION_CONTRACT_SCOPES = frozenset(("validation_context", "validation_handoff"))
_STATUS_EFFECT_TO_STATUS = {
    "select": "selected",
    "propose": "proposed",
    "hold": "held",
    "reject": "rejected",
}
_STATUS_EFFECT_PRIORITY = ("reject", "hold", "select", "propose")


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


@dataclass(frozen=True, slots=True)
class SelectedValidationContract:
    contract_id: str
    policy_profile_id: str
    ledger_id: str
    basis: str
    selected_decision_ids: tuple[str, ...] = field(default_factory=tuple)
    validation_scopes: tuple[PipelineScope, ...] = ("validation_handoff",)
    projection_candidate_decision_ids: tuple[str, ...] = field(default_factory=tuple)
    ledger_digest: str | None = None
    contract_version: str = "policy-boundary-selected-validation-contract-v1"
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("contract_id", self.contract_id)
        _require_non_empty("policy_profile_id", self.policy_profile_id)
        _require_non_empty("ledger_id", self.ledger_id)
        _require_non_empty("basis", self.basis)
        _require_non_empty("contract_version", self.contract_version)
        if self.ledger_digest is not None:
            _require_non_empty("ledger_digest", self.ledger_digest)
        for scope in self.validation_scopes:
            if scope not in PIPELINE_SCOPES:
                raise ValueError(f"unknown pipeline scope: {scope}")
            if scope not in _VALIDATION_CONTRACT_SCOPES:
                raise ValueError(f"{scope} is not a validation scope")
        for decision_id in self.selected_decision_ids:
            _require_non_empty("selected_decision_id", decision_id)
        for decision_id in self.projection_candidate_decision_ids:
            _require_non_empty("projection_candidate_decision_id", decision_id)
        _require_unique(
            "duplicate selected decision id",
            self.selected_decision_ids,
        )
        _require_unique(
            "duplicate projection candidate decision id",
            self.projection_candidate_decision_ids,
        )
        object.__setattr__(
            self,
            "selected_decision_ids",
            tuple(self.selected_decision_ids),
        )
        object.__setattr__(self, "validation_scopes", tuple(self.validation_scopes))
        object.__setattr__(
            self,
            "projection_candidate_decision_ids",
            tuple(self.projection_candidate_decision_ids),
        )
        object.__setattr__(self, "meta", tuple(self.meta))

    @classmethod
    def from_ledger(
        cls,
        *,
        contract_id: str,
        ledger: DecisionLedger,
        basis: str,
        ledger_digest: str | None = None,
        contract_version: str = "policy-boundary-selected-validation-contract-v1",
        meta: tuple[tuple[str, Any], ...] = (),
    ) -> SelectedValidationContract:
        return cls(
            contract_id=contract_id,
            policy_profile_id=ledger.policy_profile_id,
            ledger_id=ledger.ledger_id,
            basis=basis,
            selected_decision_ids=ledger.selected_validation_decision_ids(),
            projection_candidate_decision_ids=tuple(
                decision.decision_id
                for decision in ledger.decisions
                if decision.status == "selected"
                and decision.allows_scope("projection_candidate")
            ),
            ledger_digest=ledger_digest,
            contract_version=contract_version,
            meta=meta,
        )

    def allows_validation_decision(self, decision_id: str) -> bool:
        return decision_id in self.selected_decision_ids

    @property
    def authorizes_public_projection(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ConflictResolver:
    status_priority: tuple[PolicyEffectKind, ...] = _STATUS_EFFECT_PRIORITY

    def __post_init__(self) -> None:
        for effect_kind in self.status_priority:
            if effect_kind not in _STATUS_EFFECT_TO_STATUS:
                raise ValueError(f"unknown status priority effect kind: {effect_kind}")
        object.__setattr__(self, "status_priority", tuple(self.status_priority))

    def resolve_decision(
        self,
        *,
        decision_id: str,
        subject_id: str,
        effects: tuple[PolicyEffect, ...],
        target_id: str | None = None,
        retention: str = "decision_audit",
    ) -> SelectionDecision:
        _require_non_empty("decision_id", decision_id)
        _require_non_empty("subject_id", subject_id)
        effect_tuple = tuple(effects)
        for effect in effect_tuple:
            if effect.subject_id != subject_id:
                raise ValueError(
                    "effect subject mismatch: "
                    f"{effect.effect_id} has {effect.subject_id}, expected {subject_id}"
                )

        winning_status_effect = self._winning_status_effect(effect_tuple)
        denied_scopes = _unique_scopes(
            effect.scope
            for effect in effect_tuple
            if effect.effect_kind == "restrict_scope"
        )
        grants = tuple(
            ScopedGrant(
                grant_id=f"grant:{decision_id}:{effect.scope}",
                subject_id=decision_id,
                scope=effect.scope,
                basis=effect.basis,
                conditions=effect.payload,
                retention=_payload_value(effect, "retention", retention),
            )
            for effect in effect_tuple
            if effect.effect_kind == "grant_scope"
            and effect.scope is not None
            and effect.scope not in denied_scopes
        )

        return SelectionDecision(
            decision_id=decision_id,
            subject_id=subject_id,
            status=_STATUS_EFFECT_TO_STATUS[winning_status_effect.effect_kind],
            basis=winning_status_effect.basis,
            target_id=target_id,
            grants=grants,
            denied_scopes=denied_scopes,
            retention=_retention_from_effects(effect_tuple, retention),
        )

    def _winning_status_effect(
        self,
        effects: tuple[PolicyEffect, ...],
    ) -> PolicyEffect:
        for effect_kind in self.status_priority:
            for effect in effects:
                if effect.effect_kind == effect_kind:
                    return effect
        raise ValueError("no selection status effect")

    @property
    def authorizes_public_projection(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PolicyAssemblySubject:
    decision_id: str
    subject_id: str
    target_id: str | None = None
    retention: str = "decision_audit"

    def __post_init__(self) -> None:
        _require_non_empty("decision_id", self.decision_id)
        _require_non_empty("subject_id", self.subject_id)
        _require_non_empty("retention", self.retention)


@dataclass(frozen=True, slots=True)
class PolicyAssembly:
    policy_profile_id: str
    resolver: ConflictResolver = field(default_factory=ConflictResolver)

    def __post_init__(self) -> None:
        _require_non_empty("policy_profile_id", self.policy_profile_id)

    def assemble_ledger(
        self,
        *,
        ledger_id: str,
        subjects: tuple[PolicyAssemblySubject, ...],
        effects: tuple[PolicyEffect, ...],
        descriptors: tuple[MaterialDescriptor, ...] = (),
        meta: tuple[tuple[str, Any], ...] = (),
    ) -> DecisionLedger:
        _require_non_empty("ledger_id", ledger_id)
        subject_tuple = tuple(subjects)
        effect_tuple = tuple(effects)
        _require_unique(
            "duplicate policy assembly decision id",
            tuple(subject.decision_id for subject in subject_tuple),
        )
        _require_unique(
            "duplicate policy assembly subject id",
            tuple(subject.subject_id for subject in subject_tuple),
        )
        subject_ids = frozenset(subject.subject_id for subject in subject_tuple)
        for effect in effect_tuple:
            if effect.subject_id not in subject_ids:
                raise ValueError(
                    f"unassembled policy effect subject: {effect.subject_id}"
                )

        decisions = tuple(
            self._resolve_subject(subject, effect_tuple)
            for subject in subject_tuple
        )
        return DecisionLedger(
            ledger_id=ledger_id,
            policy_profile_id=self.policy_profile_id,
            descriptors=tuple(descriptors),
            effects=effect_tuple,
            decisions=decisions,
            meta=tuple(meta),
        )

    def _resolve_subject(
        self,
        subject: PolicyAssemblySubject,
        effects: tuple[PolicyEffect, ...],
    ) -> SelectionDecision:
        subject_effects = tuple(
            effect for effect in effects if effect.subject_id == subject.subject_id
        )
        if not subject_effects:
            raise ValueError(
                f"no policy effects for assembly subject: {subject.subject_id}"
            )
        return self.resolver.resolve_decision(
            decision_id=subject.decision_id,
            subject_id=subject.subject_id,
            effects=subject_effects,
            target_id=subject.target_id,
            retention=subject.retention,
        )

    @property
    def authorizes_public_projection(self) -> bool:
        return False


def _require_non_empty(field_name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")


def _require_unique(error_label: str, values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(error_label)


def _unique_scopes(scopes) -> tuple[PipelineScope, ...]:
    result = []
    for scope in scopes:
        if scope is not None and scope not in result:
            result.append(scope)
    return tuple(result)


def _payload_value(effect: PolicyEffect, key: str, default):
    for item_key, value in effect.payload:
        if item_key == key:
            return value
    return default


def _retention_from_effects(
    effects: tuple[PolicyEffect, ...],
    default: str,
) -> str:
    for effect in effects:
        if effect.effect_kind == "set_retention":
            return _payload_value(effect, "retention", effect.basis)
    return default


__all__ = [
    "PIPELINE_SCOPES",
    "POLICY_EFFECT_KINDS",
    "SELECTION_STATUSES",
    "ConflictResolver",
    "DecisionLedger",
    "MaterialDescriptor",
    "PipelineScope",
    "PolicyAssembly",
    "PolicyAssemblySubject",
    "PolicyEffect",
    "PolicyEffectKind",
    "ScopedGrant",
    "SelectionDecision",
    "SelectionStatus",
    "SelectedValidationContract",
]
