from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from comp.compiler_tool.models import ClaimCandidate, EvidenceRef, InterpretationHypothesis
from comp.policy import SelectedValidationContract


@dataclass(frozen=True, slots=True)
class ValidationHandoffClaim:
    decision_id: str
    claim: ClaimCandidate

    def __post_init__(self) -> None:
        _require_non_empty("decision_id", self.decision_id)


@dataclass(frozen=True, slots=True)
class ValidationHandoff:
    handoff_id: str
    contract: SelectedValidationContract
    hypothesis_id: str
    subject_id: str
    claims: tuple[ValidationHandoffClaim, ...] = field(default_factory=tuple)
    witnesses: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("handoff_id", self.handoff_id)
        _require_non_empty("hypothesis_id", self.hypothesis_id)
        _require_non_empty("subject_id", self.subject_id)
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "witnesses", tuple(self.witnesses))
        object.__setattr__(self, "meta", tuple(self.meta))
        self._validate_claim_decisions()

    @property
    def policy_profile_id(self) -> str:
        return self.contract.policy_profile_id

    @property
    def ledger_id(self) -> str:
        return self.contract.ledger_id

    @property
    def selected_decision_ids(self) -> tuple[str, ...]:
        return self.contract.selected_decision_ids

    def to_interpretation_hypothesis(self) -> InterpretationHypothesis:
        return InterpretationHypothesis(
            hypothesis_id=self.hypothesis_id,
            subject_id=self.subject_id,
            claims=tuple(handoff_claim.claim for handoff_claim in self.claims),
            witnesses=self.witnesses,
        )

    @property
    def authorizes_public_projection(self) -> bool:
        return False

    def _validate_claim_decisions(self) -> None:
        claim_decision_ids = tuple(claim.decision_id for claim in self.claims)
        if len(claim_decision_ids) != len(set(claim_decision_ids)):
            raise ValueError("duplicate handoff claim decision id")

        selected_decision_ids = set(self.contract.selected_decision_ids)
        for handoff_claim in self.claims:
            decision_id = handoff_claim.decision_id
            if decision_id not in selected_decision_ids:
                raise ValueError(
                    f"handoff claim decision is not selected for validation handoff: "
                    f"{decision_id}"
                )
            target_id = self.contract.target_for_validation_decision(decision_id)
            if (
                target_id is not None
                and handoff_claim.claim.field != _field_name_from_target_id(target_id)
            ):
                raise ValueError(
                    "handoff claim field does not match selected target: "
                    f"{decision_id} expects {target_id}, "
                    f"got {handoff_claim.claim.field}"
                )

        missing = tuple(
            decision_id
            for decision_id in self.contract.selected_decision_ids
            if decision_id not in claim_decision_ids
        )
        if missing:
            raise ValueError(f"missing handoff claim for selected decision: {missing[0]}")


def _require_non_empty(field_name: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required.")


def _field_name_from_target_id(target_id: str) -> str:
    if target_id.startswith("field:"):
        return target_id.split(":", 1)[1]
    return target_id


__all__ = ["ValidationHandoff", "ValidationHandoffClaim"]
