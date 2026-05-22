from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReferenceOption:
    candidate_id: str
    reference_id: str
    reference_type: str
    retrieval_method: str
    retrieval_score: float | None = None
    source: str | None = None
    witness_ids: tuple[str, ...] = field(default_factory=tuple)
    authority: str = "candidate_only"

    def __post_init__(self) -> None:
        _require_authority(
            actual=self.authority,
            expected="candidate_only",
            artifact="ReferenceOption",
        )

    @property
    def can_authorize_calculation(self) -> bool:
        return False


@dataclass(frozen=True)
class RejectedReferenceCandidate:
    candidate_id: str
    reference_id: str
    reason: str
    selector_rule_id: str | None = None


@dataclass(frozen=True)
class CanonicalReference:
    binding_id: str
    claim_id: str
    reference_id: str
    reference_type: str
    selected_candidate_id: str | None = None
    selector_rule_id: str | None = None
    source_witness_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_candidates: tuple[RejectedReferenceCandidate, ...] = field(
        default_factory=tuple
    )
    authority: str = "canonical_binding"

    def __post_init__(self) -> None:
        _require_authority(
            actual=self.authority,
            expected="canonical_binding",
            artifact="CanonicalReference",
        )

    @property
    def can_authorize_calculation(self) -> bool:
        return True


def _require_authority(*, actual: str, expected: str, artifact: str) -> None:
    if actual != expected:
        raise ValueError(f"{artifact} authority must be {expected!r}")


ReferenceCandidate = ReferenceOption
ReferenceBinding = CanonicalReference


__all__ = [
    "ReferenceOption",
    "ReferenceCandidate",
    "RejectedReferenceCandidate",
    "CanonicalReference",
    "ReferenceBinding",
]
