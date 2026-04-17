# artifacts.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class CalculationArtifact:
    calculation_id: str
    row_id: str
    frame_id: str

    row_status_at_calc: str
    calculation_status: str           # success | failed | excluded

    activity_type: Optional[str] = None

    standardized_amount: Optional[float] = None
    standardized_unit: Optional[str] = None

    factor_id: Optional[str] = None
    applied_factor: Optional[float] = None
    factor_unit: Optional[str] = None

    co2e_kg: Optional[float] = None
    scope_category: Optional[str] = None

    exclusion_reason: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GovernanceDecisionArtifact:
    decision_id: str
    row_id: str
    frame_id: str

    from_status: str
    to_status: str

    action: str              # hold | merge | skip
    actor: str               # system | human_reviewer | policy_engine
    reason_codes: list[str] = field(default_factory=list)
    matched_rule_keys: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DiagnosticArtifact:
    diagnostic_id: str

    severity: str                 # error | warning | info
    code: str
    message: str

    scope_kind: str               # frame | claim | row
    scope_id: str

    frame_id: Optional[str] = None
    claim_id: Optional[str] = None
    fragment_id: Optional[str] = None
    span: Optional[tuple[int, int]] = None

    rule_kind: Optional[str] = None   # require | forbid | diagnostic | inference
    source_key: Optional[str] = None  # e.g. require:3, warning:AggregateRow
    phase: Optional[str] = None       # semantic_pre / semantic_post / inference

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TokenOccurrence:
    token_id: str
    token_name: str
    fragment_id: str

    value: Any
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: float = 0.0

    source_channel: str = "primary"   # primary | fallback
    used_llm: bool = False
    rank: int = 0

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ClaimArtifact:
    claim_id: str
    frame_id: str
    fragment_id: str
    parser_name: str

    role_name: str
    value: Any
    normalized_value: Any = None

    extraction_mode: str = "explicit"   # explicit | inherited | backward_inferred | derived
    confidence: float = 0.0

    candidate_state: str = "shadow"     # active | shadow | frozen | rejected
    status: str = "resolving"

    source_token_id: Optional[str] = None
    source_fragment_id: Optional[str] = None
    span: Optional[tuple[int, int]] = None

    reason_codes: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoleSlotArtifact:
    role_name: str

    active_claim_id: Optional[str] = None
    shadow_claim_ids: list[str] = field(default_factory=list)
    frozen_claim_ids: list[str] = field(default_factory=list)
    rejected_claim_ids: list[str] = field(default_factory=list)

    resolved_value: Any = None
    confidence: float = 0.0

    missing_tag: Optional[str] = None   # missing_waiting_context / missing_parser_failed ...
    reason_codes: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameRuntimeState:
    resolution_score: float = 0.0
    iteration_count: int = 0
    stable_count: int = 0
    termination_reason: Optional[str] = None


@dataclass
class PartialFrameArtifact:
    frame_id: str
    parser_name: str
    frame_type: str

    fragment_ids: list[str] = field(default_factory=list)
    slots: dict[str, RoleSlotArtifact] = field(default_factory=dict)

    diagnostics: list[DiagnosticArtifact] = field(default_factory=list)
    status: str = "resolving"
    runtime: FrameRuntimeState = field(default_factory=FrameRuntimeState)

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompileArtifacts:
    fragments: list[Any] = field(default_factory=list)
    tokens: list[TokenOccurrence] = field(default_factory=list)
    claims: list[ClaimArtifact] = field(default_factory=list)
    frames: list[PartialFrameArtifact] = field(default_factory=list)
    rows: list[CanonicalRowArtifact] = field(default_factory=list)
    calculations: list[CalculationArtifact] = field(default_factory=list)

    diagnostics: list[DiagnosticArtifact] = field(default_factory=list)
    event_log: list[Any] = field(default_factory=list)
    commit_log: list[Any] = field(default_factory=list)
    merge_log: list[GovernanceDecisionArtifact] = field(default_factory=list)


def diagnostic_codes(
    diagnostics: list[DiagnosticArtifact],
    *,
    severity: str,
) -> list[str]:
    codes: set[str] = set()
    for diag in diagnostics:
        if not isinstance(diag, DiagnosticArtifact):
            raise TypeError("diagnostics must contain DiagnosticArtifact only")
        if diag.severity == severity and diag.code:
            codes.add(diag.code)
    return sorted(codes)


def warning_codes_from_diagnostics(diagnostics: list[DiagnosticArtifact]) -> list[str]:
    return diagnostic_codes(diagnostics, severity="warning")


def error_codes_from_diagnostics(diagnostics: list[DiagnosticArtifact]) -> list[str]:
    return diagnostic_codes(diagnostics, severity="error")


@dataclass
class LineageEvidenceArtifact:
    claim_id: str
    fragment_id: Optional[str] = None
    span: Optional[tuple[int, int]] = None
    extraction_mode: str = "explicit"

    value: Any = None
    reason_codes: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoleLineageArtifact:
    direct: list[LineageEvidenceArtifact] = field(default_factory=list)
    inherited: list[LineageEvidenceArtifact] = field(default_factory=list)
    backward_inferred: list[LineageEvidenceArtifact] = field(default_factory=list)
    derived: list[LineageEvidenceArtifact] = field(default_factory=list)
    contradicted_by: list[LineageEvidenceArtifact] = field(default_factory=list)


@dataclass
class CanonicalRowArtifact:
    row_id: str
    frame_id: str
    parser_name: str
    frame_type: str

    status: str = "committed"

    site_id: Optional[str] = None
    entity_id: Optional[str] = None
    period: Optional[str] = None
    activity_type: Optional[str] = None

    raw_amount: Optional[float] = None
    raw_unit: Optional[str] = None

    standardized_amount: Optional[float] = None
    standardized_unit: Optional[str] = None

    scope_category: Optional[str] = None
    resolution_score: float = 0.0

    lineage: dict[str, RoleLineageArtifact] = field(default_factory=dict)

    source_fragment_ids: list[str] = field(default_factory=list)
    warning_codes: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
