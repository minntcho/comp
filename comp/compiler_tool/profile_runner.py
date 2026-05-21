from __future__ import annotations

from comp.compiler_tool.models import (
    ClaimHypothesis,
    CompileReport,
    EvidenceWitness,
    FailedClaim,
    InterpretationHypothesis,
    ProofObligation,
)
from comp.compiler_tool.profiles import CompilerProfile, active_rule_families, validate_compiler_profile
from comp.compiler_tool.report_status import with_recomputed_status


def compile_with_profile(
    hypothesis: InterpretationHypothesis,
    profile: CompilerProfile,
) -> CompileReport:
    validate_compiler_profile(profile)
    failed_claims: list[FailedClaim] = []
    obligations: list[ProofObligation] = []
    witnesses = {witness.witness_id: witness for witness in hypothesis.witnesses}

    for claim in hypothesis.claims:
        witness_failure = _validate_core_witness(claim, witnesses)
        if witness_failure is not None:
            failed_claims.append(witness_failure)
            _add_obligation(
                obligations,
                ProofObligation(
                    kind="find_source_witness",
                    field=claim.field,
                    reason=witness_failure.reason,
                ),
            )

        for rule in active_rule_families(profile, validate=False):
            if rule.evaluate is None:
                continue
            for result in rule.evaluate(claim, hypothesis, profile):
                if isinstance(result, ProofObligation):
                    _add_obligation(obligations, result)

    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=hypothesis.witnesses,
            failed_claims=tuple(failed_claims),
            obligations=tuple(obligations),
            can_project_public_row=False,
        )
    )


def _validate_core_witness(
    claim: ClaimHypothesis,
    witnesses: dict[str, EvidenceWitness],
) -> FailedClaim | None:
    if claim.value is None:
        return None

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


def _add_obligation(
    obligations: list[ProofObligation],
    obligation: ProofObligation,
) -> None:
    if obligation not in obligations:
        obligations.append(obligation)


__all__ = ["compile_with_profile"]
