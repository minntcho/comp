from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from comp.compiler_tool.models import (
    ClaimCandidate,
    ValidationReport,
    EvidenceRef,
    FailedClaim,
    InterpretationHypothesis,
    ValidationRequirement,
)
from comp.compiler_tool.profiles import (
    CompilerProfile,
    active_rule_families,
    profile_allowed_units,
    profile_known_fields,
    validate_compiler_profile,
)
from comp.compiler_tool.report_status import with_recomputed_status
from comp.compiler_tool.tool import CompilerTool


T = TypeVar("T")


def run_profile_rules(
    hypothesis: InterpretationHypothesis,
    profile: CompilerProfile,
) -> ValidationReport:
    """Run profile-active rules without taking over the CompilerTool baseline.

    This runner validates core source-witness grounding for submitted claims, then
    asks active profile rule evaluators to open obligations. It does not apply
    CompilerTool construction-time policy such as known-field coverage,
    allowed-unit filtering, or missing-unit hazards.
    """

    validate_compiler_profile(profile)
    failed_claims: list[FailedClaim] = []
    obligations: list[ValidationRequirement] = []
    witnesses = {witness.witness_id: witness for witness in hypothesis.witnesses}

    for claim in hypothesis.claims:
        witness_failure = _validate_core_witness(claim, witnesses)
        if witness_failure is not None:
            failed_claims.append(witness_failure)
            _add_obligation(
                obligations,
                ValidationRequirement(
                    kind="find_source_witness",
                    field=claim.field,
                    reason=witness_failure.reason,
                ),
            )

        for rule in active_rule_families(profile, validate=False):
            if rule.evaluate is None:
                continue
            for result in rule.evaluate(claim, hypothesis, profile):
                if isinstance(result, ValidationRequirement):
                    _add_obligation(obligations, result)

    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=hypothesis.witnesses,
            failed_claims=tuple(failed_claims),
            validation_requirements=tuple(obligations),
            can_build_public_output=False,
        )
    )


def compile_with_profile(
    hypothesis: InterpretationHypothesis,
    profile: CompilerProfile,
) -> ValidationReport:
    """Compile with profile-declared CompilerTool baseline plus active rules."""

    validate_compiler_profile(profile)
    baseline_report = CompilerTool(
        allowed_units=profile_allowed_units(profile, validate=False),
        known_fields=profile_known_fields(profile, validate=False),
    ).compile_interpretation(hypothesis)
    profile_rule_report = run_profile_rules(hypothesis, profile)
    return _merge_compile_reports(baseline_report, profile_rule_report)


def _validate_core_witness(
    claim: ClaimCandidate,
    witnesses: dict[str, EvidenceRef],
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
    obligations: list[ValidationRequirement],
    obligation: ValidationRequirement,
) -> None:
    if obligation not in obligations:
        obligations.append(obligation)


def _merge_compile_reports(
    baseline_report: ValidationReport,
    profile_rule_report: ValidationReport,
) -> ValidationReport:
    return with_recomputed_status(
        replace(
            baseline_report,
            evidence_refs=_merge_unique(
                baseline_report.evidence_refs,
                profile_rule_report.evidence_refs,
            ),
            checked_claims=_merge_unique(
                baseline_report.checked_claims,
                profile_rule_report.checked_claims,
            ),
            failed_claims=_merge_unique(
                baseline_report.failed_claims,
                profile_rule_report.failed_claims,
            ),
            unknowns=_merge_unique(
                baseline_report.unknowns,
                profile_rule_report.unknowns,
            ),
            unchecked_areas=_merge_unique(
                baseline_report.unchecked_areas,
                profile_rule_report.unchecked_areas,
            ),
            validation_requirements=_merge_unique(
                baseline_report.validation_requirements,
                profile_rule_report.validation_requirements,
            ),
            resolved_validation_requirements=_merge_unique(
                baseline_report.resolved_validation_requirements,
                profile_rule_report.resolved_validation_requirements,
            ),
            hazards=_merge_unique(
                baseline_report.hazards,
                profile_rule_report.hazards,
            ),
            reference_options=_merge_unique(
                baseline_report.reference_options,
                profile_rule_report.reference_options,
            ),
            canonical_references=_merge_unique(
                baseline_report.canonical_references,
                profile_rule_report.canonical_references,
            ),
            calculated_claims=_merge_unique(
                baseline_report.calculated_claims,
                profile_rule_report.calculated_claims,
            ),
            can_build_public_output=(
                baseline_report.can_build_public_output
                and profile_rule_report.can_build_public_output
            ),
        )
    )


def _merge_unique(first: tuple[T, ...], second: tuple[T, ...]) -> tuple[T, ...]:
    merged = list(first)
    for item in second:
        if item not in merged:
            merged.append(item)
    return tuple(merged)


__all__ = ["compile_with_profile", "run_profile_rules"]
