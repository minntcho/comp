from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ReportStatus = Literal[
    "accepted",
    "blocked",
    "review_required",
    "underconstrained",
    "unchecked",
]


@dataclass(frozen=True, slots=True)
class EvidenceWitness:
    witness_id: str
    field: str
    source: str | None = None
    span: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class ClaimHypothesis:
    field: str
    value: Any
    witness_id: str | None = None
    origin: str = "llm_inferred"


@dataclass(frozen=True, slots=True)
class Hazard:
    kind: str
    field: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class InterpretationHypothesis:
    hypothesis_id: str
    claims: tuple[ClaimHypothesis, ...] = ()
    witnesses: tuple[EvidenceWitness, ...] = ()
    hazards: tuple[Hazard, ...] = ()


@dataclass(frozen=True, slots=True)
class CheckedClaim:
    field: str
    value: Any
    witness_id: str


@dataclass(frozen=True, slots=True)
class FailedClaim:
    field: str
    value: Any
    reason: str
    origin: str = "llm_inferred"


@dataclass(frozen=True, slots=True)
class UnknownClaim:
    field: str
    reason: str
    required_context: str | None = None


@dataclass(frozen=True, slots=True)
class UncheckedArea:
    area: str
    reason: str = "missing_rule_coverage"


@dataclass(frozen=True, slots=True)
class ProofObligation:
    kind: str
    field: str | None = None
    acceptable_sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompileReport:
    status: ReportStatus
    passed_claims: tuple[CheckedClaim, ...] = ()
    failed_claims: tuple[FailedClaim, ...] = ()
    unknowns: tuple[UnknownClaim, ...] = ()
    unchecked_areas: tuple[UncheckedArea, ...] = ()
    obligations: tuple[ProofObligation, ...] = ()
    hazards: tuple[Hazard, ...] = ()
    receipt_preconditions: tuple[str, ...] = ()
    can_project_public_row: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
