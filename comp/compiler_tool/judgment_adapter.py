from __future__ import annotations

from comp.compiler_tool.models import CompileReport, ProofObligation
from comp.judgment import Fact, FactTag, JudgmentState, SubjectRef


def compile_report_to_facts(report: CompileReport, subject: SubjectRef) -> set[Fact]:
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

    for claim in report.derived_claims:
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

    for obligation in report.obligations:
        facts.add(_obligation_fact("hazard_open", report.status, subject, obligation))

    for obligation in report.resolved_obligations:
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
    state: JudgmentState, report: CompileReport, subject: SubjectRef
) -> set[Fact]:
    return state.add_facts(compile_report_to_facts(report, subject))


def _obligation_fact(
    tag: FactTag,
    status: str,
    subject: SubjectRef,
    obligation: ProofObligation,
    *,
    section: str = "proof_obligation",
) -> Fact:
    return Fact(
        tag=tag,
        subject=subject,
        key=f"proof_obligation:{obligation.field}",
        value=_obligation_id(obligation.kind, obligation.field, obligation.reason),
        meta=(
            ("kind", obligation.kind),
            ("reason", obligation.reason),
            ("report_section", section),
            ("report_status", status),
        ),
    )


def _failed_claim_id(field: str, reason: str) -> str:
    return _stable_id("failed_claim", field, reason)


def _unknown_claim_id(field: str, reason: str) -> str:
    return _stable_id("unknown_claim", field, reason)


def _unchecked_area_id(field: str, reason: str) -> str:
    return _stable_id("unchecked_area", field, reason)


def _obligation_id(kind: str, field: str, reason: str) -> str:
    return _stable_id("proof_obligation", kind, field, reason)


def _hazard_id(kind: str, field: str, severity: str) -> str:
    return _stable_id("hazard", kind, field, severity)


def _stable_id(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


__all__ = [
    "compile_report_to_facts",
    "add_compile_report_facts",
]
