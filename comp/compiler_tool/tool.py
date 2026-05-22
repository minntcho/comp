from __future__ import annotations

from comp.compiler_tool.models import (
    CheckedClaim,
    ClaimCandidate,
    ValidationReport,
    EvidenceRef,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ValidationRequirement,
    UncheckedArea,
    UnknownClaim,
)
from comp.compiler_tool.report_status import with_recomputed_status


class CompilerTool:
    """Deterministic obligation oracle for interpretation hypotheses."""

    def __init__(
        self,
        *,
        allowed_units: frozenset[str] = frozenset(),
        known_fields: frozenset[str] = frozenset(),
    ) -> None:
        self.allowed_units = frozenset(unit.lower() for unit in allowed_units)
        self.known_fields = known_fields

    def compile_interpretation(
        self,
        hypothesis: InterpretationHypothesis,
    ) -> ValidationReport:
        witnesses = {witness.witness_id: witness for witness in hypothesis.witnesses}
        checked: list[CheckedClaim] = []
        failed: list[FailedClaim] = []
        unknowns: list[UnknownClaim] = []
        unchecked: list[UncheckedArea] = []
        obligations: list[ValidationRequirement] = []
        hazards: list[Hazard] = []

        claim_fields = {claim.field for claim in hypothesis.claims}

        for claim in hypothesis.claims:
            if claim.field not in self.known_fields:
                unchecked.append(
                    UncheckedArea(
                        field=claim.field,
                        reason="missing_rule_coverage",
                    )
                )
                self._add_obligation(
                    obligations,
                    ValidationRequirement(
                        kind="define_rule_coverage",
                        field=claim.field,
                        reason="missing_rule_coverage",
                    ),
                )
                continue

            if claim.value is None:
                unknowns.append(
                    UnknownClaim(field=claim.field, reason="context_required")
                )
                self._add_obligation(
                    obligations,
                    ValidationRequirement(
                        kind="find_context",
                        field=claim.field,
                        reason="context_required",
                    ),
                )
                continue

            witness_failure = self._validate_witness(claim, witnesses)
            if witness_failure is not None:
                failed.append(witness_failure)
                self._add_find_source_witness(obligations, claim.field, witness_failure.reason)
                continue

            if claim.field == "unit" and str(claim.value).lower() not in self.allowed_units:
                failed.append(
                    FailedClaim(
                        field=claim.field,
                        value=claim.value,
                        reason="unsupported_unit",
                        origin=claim.origin,
                        witness_id=claim.witness_id,
                    )
                )
                self._add_find_source_witness(obligations, claim.field, "unsupported_unit")
                continue

            checked.append(
                CheckedClaim(
                    field=claim.field,
                    value=claim.value,
                    witness_id=claim.witness_id or "",
                    origin=claim.origin,
                )
            )

        if "unit" in self.known_fields and "unit" not in claim_fields:
            hazards.append(Hazard(kind="missing_unit", field="unit", severity="review"))
            self._add_find_source_witness(obligations, "unit", "missing_unit")

        return with_recomputed_status(
            ValidationReport(
                status="accepted",
                evidence_witnesses=tuple(hypothesis.witnesses),
                checked_claims=tuple(checked),
                failed_claims=tuple(failed),
                unknowns=tuple(unknowns),
                unchecked_areas=tuple(unchecked),
                obligations=tuple(obligations),
                hazards=tuple(hazards),
                can_build_public_output=False,
            )
        )

    @staticmethod
    def _validate_witness(
        claim: ClaimCandidate,
        witnesses: dict[str, EvidenceRef],
    ) -> FailedClaim | None:
        if claim.witness_id is None:
            return FailedClaim(
                field=claim.field,
                value=claim.value,
                reason="missing_source_witness",
                origin=claim.origin,
                witness_id=None,
            )

        witness = witnesses.get(claim.witness_id)
        if witness is None:
            return FailedClaim(
                field=claim.field,
                value=claim.value,
                reason="missing_source_witness",
                origin=claim.origin,
                witness_id=claim.witness_id,
            )

        if witness.field != claim.field:
            return FailedClaim(
                field=claim.field,
                value=claim.value,
                reason="witness_field_mismatch",
                origin=claim.origin,
                witness_id=claim.witness_id,
            )

        if not witness.grounded:
            return FailedClaim(
                field=claim.field,
                value=claim.value,
                reason="ungrounded_source_witness",
                origin=claim.origin,
                witness_id=claim.witness_id,
            )

        return None

    @staticmethod
    def _add_find_source_witness(
        obligations: list[ValidationRequirement],
        field: str,
        reason: str,
    ) -> None:
        CompilerTool._add_obligation(
            obligations,
            ValidationRequirement(kind="find_source_witness", field=field, reason=reason),
        )

    @staticmethod
    def _add_obligation(
        obligations: list[ValidationRequirement],
        obligation: ValidationRequirement,
    ) -> None:
        if obligation not in obligations:
            obligations.append(obligation)
