from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from comp.compiler_tool.reference_db import ReferenceCatalog, ReferenceLookupError
from comp.compiler_tool.references import (
    CanonicalReference,
    ReferenceOption,
    RejectedReferenceOption,
)


@dataclass(frozen=True)
class ReferenceSelectionCriteria:
    binding_id: str
    claim_id: str
    reference_type: str
    selector_rule_id: str
    required_attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReferenceSelectionResult:
    status: str
    binding: CanonicalReference | None = None
    accepted_candidate_ids: tuple[str, ...] = field(default_factory=tuple)
    rejected_candidates: tuple[RejectedReferenceOption, ...] = field(
        default_factory=tuple
    )


def select_reference_binding(
    *,
    candidates: tuple[ReferenceOption, ...],
    catalog: ReferenceCatalog,
    criteria: ReferenceSelectionCriteria,
) -> ReferenceSelectionResult:
    accepted: list[tuple[ReferenceOption, tuple[str, ...]]] = []
    rejected: list[RejectedReferenceOption] = []

    for candidate in candidates:
        rejection = _rejection_reason(candidate, catalog, criteria)
        if rejection is not None:
            rejected.append(
                RejectedReferenceOption(
                    candidate_id=candidate.candidate_id,
                    reference_id=candidate.reference_id,
                    reason=rejection,
                    selector_rule_id=criteria.selector_rule_id,
                )
            )
            continue

        record = catalog.get(candidate.reference_id)
        accepted.append((candidate, record.witness_ids))

    if len(accepted) != 1:
        return ReferenceSelectionResult(
            status="ambiguous" if accepted else "no_match",
            accepted_candidate_ids=tuple(
                candidate.candidate_id for candidate, _ in accepted
            ),
            rejected_candidates=tuple(rejected),
        )

    selected, witness_ids = accepted[0]
    binding = CanonicalReference(
        binding_id=criteria.binding_id,
        claim_id=criteria.claim_id,
        reference_id=selected.reference_id,
        reference_type=criteria.reference_type,
        selected_candidate_id=selected.candidate_id,
        selector_rule_id=criteria.selector_rule_id,
        source_witness_ids=witness_ids,
        rejected_candidates=tuple(rejected),
    )
    return ReferenceSelectionResult(
        status="bound",
        binding=binding,
        accepted_candidate_ids=(selected.candidate_id,),
        rejected_candidates=tuple(rejected),
    )


def _rejection_reason(
    candidate: ReferenceOption,
    catalog: ReferenceCatalog,
    criteria: ReferenceSelectionCriteria,
) -> str | None:
    if candidate.reference_type != criteria.reference_type:
        return "reference_type_mismatch"

    try:
        record = catalog.get(candidate.reference_id)
    except ReferenceLookupError:
        return "unknown_reference"

    if record.reference_type != criteria.reference_type:
        return "reference_type_mismatch"

    for name, expected in criteria.required_attributes:
        if record.attribute(name) != expected:
            return f"attribute_mismatch:{name}"

    return None


__all__ = [
    "ReferenceSelectionCriteria",
    "ReferenceSelectionResult",
    "select_reference_binding",
]
