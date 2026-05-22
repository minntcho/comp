from __future__ import annotations

from comp.compiler_tool.commit_flow import CommitPreparation
from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.judgment import Fact, FactTag, JudgmentState, SubjectRef


def compile_report_to_facts(report: ValidationReport, subject: SubjectRef) -> set[Fact]:
    facts: set[Fact] = set()

    for claim in report.checked_claims:
        facts.add(
            Fact(
                tag="evidence",
                subject=subject,
                key=claim.field,
                value=claim.value,
                witness=claim.witness_id,
                weight=1.0,
                meta=(
                    ("origin", claim.origin),
                    ("report_section", "checked_claim"),
                    ("report_status", report.status),
                ),
            )
        )

    for claim in report.calculated_claims:
        facts.add(
            Fact(
                tag="evidence",
                subject=subject,
                key=claim.field,
                value=claim.value,
                witness=claim.trace.trace_id,
                weight=1.0,
                meta=(
                    ("claim_id", claim.claim_id),
                    ("formula_id", claim.formula_id),
                    ("input_claim_ids", claim.trace.input_claim_ids),
                    ("origin", claim.origin),
                    ("reference_binding_ids", claim.trace.reference_binding_ids),
                    ("report_section", "derived_claim"),
                    ("report_status", report.status),
                    ("trace_id", claim.trace.trace_id),
                    ("unit", claim.unit),
                ),
            )
        )

    for binding in report.canonical_references:
        facts.add(
            Fact(
                tag="prov_edge",
                subject=subject,
                key=f"reference_binding:{binding.binding_id}",
                value=binding.reference_id,
                witness=binding.selected_candidate_id,
                weight=1.0,
                meta=(
                    ("authority", binding.authority),
                    ("binding_id", binding.binding_id),
                    ("claim_id", binding.claim_id),
                    ("reference_type", binding.reference_type),
                    (
                        "rejected_candidates",
                        tuple(
                            (candidate.candidate_id, candidate.reason)
                            for candidate in binding.rejected_candidates
                        ),
                    ),
                    ("report_section", "reference_binding"),
                    ("report_status", report.status),
                    ("selector_rule_id", binding.selector_rule_id),
                    ("source_witness_ids", binding.source_witness_ids),
                ),
            )
        )

    for claim in report.failed_claims:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"failed_claim:{claim.field}",
                value=_failed_claim_id(claim.field, claim.reason),
                witness=claim.witness_id,
                meta=(
                    ("origin", claim.origin),
                    ("reason", claim.reason),
                    ("report_section", "failed_claim"),
                    ("report_status", report.status),
                ),
            )
        )

    for unknown in report.unknowns:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"unknown_claim:{unknown.field}",
                value=_unknown_claim_id(unknown.field, unknown.reason),
                meta=(
                    ("reason", unknown.reason),
                    ("report_section", "unknown_claim"),
                    ("report_status", report.status),
                ),
            )
        )

    for unchecked in report.unchecked_areas:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"unchecked_area:{unchecked.field}",
                value=_unchecked_area_id(unchecked.field, unchecked.reason),
                meta=(
                    ("reason", unchecked.reason),
                    ("report_section", "unchecked_area"),
                    ("report_status", report.status),
                ),
            )
        )

    for obligation in report.validation_requirements:
        facts.add(_obligation_fact("hazard_open", report.status, subject, obligation))

    for obligation in report.resolved_validation_requirements:
        facts.add(
            _obligation_fact(
                "hazard_discharge",
                report.status,
                subject,
                obligation,
                section="resolved_obligation",
            )
        )

    for hazard in report.hazards:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"hazard:{hazard.field}",
                value=_hazard_id(hazard.kind, hazard.field, hazard.severity),
                meta=(
                    ("kind", hazard.kind),
                    ("report_section", "hazard"),
                    ("report_status", report.status),
                    ("severity", hazard.severity),
                ),
            )
        )

    return facts


def add_compile_report_facts(
    state: JudgmentState, report: ValidationReport, subject: SubjectRef
) -> set[Fact]:
    return state.add_facts(compile_report_to_facts(report, subject))


def commit_preparation_to_facts(
    preparation: CommitPreparation, subject: SubjectRef
) -> set[Fact]:
    package = preparation.package
    decision = preparation.decision
    facts = {
        Fact(
            tag="prov_edge",
            subject=subject,
            key="commit_package",
            value=package.package_id,
            meta=(
                ("checked_claim_fields", package.checked_claim_fields),
                ("checked_claim_witness_ids", package.checked_claim_witness_ids),
                ("calculation_trace_ids", package.calculation_trace_ids),
                ("complete", package.complete),
                ("derived_claim_fields", package.derived_claim_fields),
                ("derived_claim_ids", package.derived_claim_ids),
                ("formula_ids", package.formula_ids),
                ("hazard_ids", package.hazard_ids),
                ("open_obligation_ids", package.open_obligation_ids),
                ("profile_id", package.profile_id),
                ("reference_binding_ids", package.reference_binding_ids),
                ("report_status", package.report_status),
                ("resolved_obligation_ids", package.resolved_obligation_ids),
                ("semantic_judgment_ids", package.semantic_judgment_ids),
            ),
        ),
        Fact(
            tag="prov_edge",
            subject=subject,
            key="governance_decision",
            value=decision.decision_id,
            meta=(
                ("can_issue_commit_receipt", decision.can_issue_commit_receipt),
                ("governance_reasons", decision.reasons),
                ("governance_status", decision.status),
                ("package_id", decision.package_id),
                ("profile_id", decision.profile_id),
            ),
        ),
    }

    for obligation_id in package.open_obligation_ids:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"commit_obligation:{obligation_id}",
                value=obligation_id,
                meta=(("report_section", "commit_package"),),
            )
        )

    for hazard_id in package.hazard_ids:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=subject,
                key=f"commit_hazard:{hazard_id}",
                value=hazard_id,
                meta=(("report_section", "commit_package"),),
            )
        )

    if preparation.receipt is not None:
        facts.add(
            Fact(
                tag="prov_edge",
                subject=subject,
                key="commit_receipt",
                value=preparation.receipt.public_row_id,
                witness=decision.decision_id,
                meta=(
                    ("commit_package_id", package.package_id),
                    ("projection_id", preparation.receipt.projection_id),
                    ("authorized_fields", preparation.receipt.authorized_fields),
                    ("receipt_snapshot", preparation.receipt.barrier_snapshot),
                ),
            )
        )

    return facts


def add_commit_preparation_facts(
    state: JudgmentState,
    preparation: CommitPreparation,
    subject: SubjectRef,
) -> set[Fact]:
    return state.add_facts(commit_preparation_to_facts(preparation, subject))


def _obligation_fact(
    tag: FactTag,
    status: str,
    subject: SubjectRef,
    obligation: ValidationRequirement,
    *,
    section: str = "proof_obligation",
) -> Fact:
    meta = [
        ("kind", obligation.kind),
        ("reason", obligation.reason),
    ]
    if obligation.calculation_requirement is not None:
        meta.extend(
            _calculation_requirement_meta(obligation.calculation_requirement)
        )
    meta.extend(
        [
            ("report_section", section),
            ("report_status", status),
        ]
    )
    return Fact(
        tag=tag,
        subject=subject,
        key=f"proof_obligation:{obligation.field}",
        value=_obligation_id(obligation),
        meta=tuple(meta),
    )


def _failed_claim_id(field: str, reason: str) -> str:
    return _stable_id("failed_claim", field, reason)


def _unknown_claim_id(field: str, reason: str) -> str:
    return _stable_id("unknown_claim", field, reason)


def _unchecked_area_id(field: str, reason: str) -> str:
    return _stable_id("unchecked_area", field, reason)


def _obligation_id(obligation: ValidationRequirement) -> str:
    if obligation.obligation_id is not None:
        return obligation.obligation_id
    return _stable_id(
        "proof_obligation",
        obligation.kind,
        obligation.field,
        obligation.reason,
    )


def _hazard_id(kind: str, field: str, severity: str) -> str:
    return _stable_id("hazard", kind, field, severity)


def _calculation_requirement_meta(requirement) -> list[tuple[str, str]]:
    return [
        (key, value)
        for key, value in (
            ("actual_output_unit", requirement.actual_output_unit),
            ("actual_unit", requirement.actual_unit),
            ("expected_output_unit", requirement.expected_output_unit),
            ("expected_unit", requirement.expected_unit),
            ("formula_id", requirement.formula_id),
            ("input_claim_id", requirement.input_claim_id),
            ("missing_attribute", requirement.missing_attribute),
            ("output_claim_id", requirement.output_claim_id),
            ("reference_binding_id", requirement.reference_binding_id),
            ("reference_id", requirement.reference_id),
        )
        if value is not None
    ]


def _stable_id(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


__all__ = [
    "compile_report_to_facts",
    "add_compile_report_facts",
    "commit_preparation_to_facts",
    "add_commit_preparation_facts",
]
