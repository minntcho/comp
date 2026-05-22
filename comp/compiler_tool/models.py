from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from comp.compiler_tool.calculations import CalculationRequirement, CalculatedClaim
from comp.compiler_tool.references import CanonicalReference, ReferenceOption
from comp.judgment.receipts import DependencyFingerprint

CompileStatus = Literal[
    "accepted",
    "blocked",
    "review_required",
    "underconstrained",
    "unchecked",
]


@dataclass(frozen=True)
class ClaimCandidate:
    field: str
    value: Any
    witness_id: str | None = None
    origin: str = "llm_inferred"



@dataclass(frozen=True)
class EvidenceRef:
    witness_id: str
    field: str
    source: str | None = None
    span: str | None = None
    text: str | None = None

    @property
    def grounded(self) -> bool:
        return self.source is not None or self.span is not None



def evidence_ref_fingerprint(witness: EvidenceRef) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="evidence_witness",
        dependency_id=witness.witness_id,
        payload={
            "witness_id": witness.witness_id,
            "field": witness.field,
            "source": witness.source,
            "span": witness.span,
            "text": witness.text,
        },
    )



@dataclass(frozen=True)
class InterpretationHypothesis:
    hypothesis_id: str
    subject_id: str
    claims: tuple[ClaimCandidate, ...] = field(default_factory=tuple)
    witnesses: tuple[EvidenceRef, ...] = field(default_factory=tuple)


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
class ValidationRequirement:
    kind: str
    field: str
    reason: str
    obligation_id: str | None = None
    claim_id: str | None = None
    blocking: bool = True
    semantic_requirement: SemanticJudgmentRequirement | None = None
    calculation_requirement: CalculationRequirement | None = None



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
class ValidationReport:
    status: CompileStatus
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    checked_claims: tuple[CheckedClaim, ...] = field(default_factory=tuple)
    failed_claims: tuple[FailedClaim, ...] = field(default_factory=tuple)
    unknowns: tuple[UnknownClaim, ...] = field(default_factory=tuple)
    unchecked_areas: tuple[UncheckedArea, ...] = field(default_factory=tuple)
    validation_requirements: tuple[ValidationRequirement, ...] = field(default_factory=tuple)
    resolved_validation_requirements: tuple[ValidationRequirement, ...] = field(default_factory=tuple)
    hazards: tuple[Hazard, ...] = field(default_factory=tuple)
    reference_options: tuple[ReferenceOption, ...] = field(default_factory=tuple)
    canonical_references: tuple[CanonicalReference, ...] = field(default_factory=tuple)
    calculated_claims: tuple[CalculatedClaim, ...] = field(default_factory=tuple)
    can_build_public_output: bool = False
