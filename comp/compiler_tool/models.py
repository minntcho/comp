from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from comp.compiler_tool.calculations import DerivedClaim
from comp.compiler_tool.references import ReferenceBinding, ReferenceCandidate

CompileStatus = Literal[
    "accepted",
    "blocked",
    "review_required",
    "underconstrained",
    "unchecked",
]


@dataclass(frozen=True)
class ClaimHypothesis:
    field: str
    value: Any
    witness_id: str | None = None
    origin: str = "llm_inferred"


@dataclass(frozen=True)
class EvidenceWitness:
    witness_id: str
    field: str
    source: str | None = None
    span: str | None = None
    text: str | None = None

    @property
    def grounded(self) -> bool:
        return self.source is not None or self.span is not None


@dataclass(frozen=True)
class InterpretationHypothesis:
    hypothesis_id: str
    subject_id: str
    claims: tuple[ClaimHypothesis, ...] = field(default_factory=tuple)
    witnesses: tuple[EvidenceWitness, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CheckedClaim:
    field: str
    value: Any
    witness_id: str
    origin: str


@dataclass(frozen=True)
class FailedClaim:
    field: str
    value: Any
    reason: str
    origin: str
    witness_id: str | None = None


@dataclass(frozen=True)
class UnknownClaim:
    field: str
    reason: str


@dataclass(frozen=True)
class UncheckedArea:
    field: str
    reason: str


@dataclass(frozen=True)
class SemanticJudgmentRequirement:
    question: str
    claim_id: str
    evidence_span_ids: tuple[str, ...] = field(default_factory=tuple)
    rubric_id: str = ""
    acceptable_verdicts: tuple[str, ...] = field(default_factory=tuple)
    required_verdict: str = "supports"
    allowed_judges: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProofObligation:
    kind: str
    field: str
    reason: str
    obligation_id: str | None = None
    claim_id: str | None = None
    blocking: bool = True
    semantic_requirement: SemanticJudgmentRequirement | None = None


@dataclass(frozen=True)
class SemanticJudgment:
    judgment_id: str
    obligation_id: str
    verdict: str
    rubric_id: str
    judge: str
    cited_span_ids: tuple[str, ...]
    rationale: str
    confidence: float | None = None


@dataclass(frozen=True)
class Hazard:
    kind: str
    field: str
    severity: str


@dataclass(frozen=True)
class CompileReport:
    status: CompileStatus
    checked_claims: tuple[CheckedClaim, ...] = field(default_factory=tuple)
    failed_claims: tuple[FailedClaim, ...] = field(default_factory=tuple)
    unknowns: tuple[UnknownClaim, ...] = field(default_factory=tuple)
    unchecked_areas: tuple[UncheckedArea, ...] = field(default_factory=tuple)
    obligations: tuple[ProofObligation, ...] = field(default_factory=tuple)
    resolved_obligations: tuple[ProofObligation, ...] = field(default_factory=tuple)
    hazards: tuple[Hazard, ...] = field(default_factory=tuple)
    reference_candidates: tuple[ReferenceCandidate, ...] = field(default_factory=tuple)
    reference_bindings: tuple[ReferenceBinding, ...] = field(default_factory=tuple)
    derived_claims: tuple[DerivedClaim, ...] = field(default_factory=tuple)
    can_project_public_row: bool = False
