from __future__ import annotations

from comp.compiler_tool.models import CompileReport
from comp.judgment import Fact, SubjectRef


def compile_report_to_facts(report: CompileReport, *, subject_id: str) -> set[Fact]:
    facts: set[Fact] = set()

    for claim in report.passed_claims:
        facts.add(
            Fact(
                tag="evidence",
                subject=SubjectRef("claim", f"{subject_id}:{claim.field}"),
                key=claim.field,
                value=claim.value,
                witness=claim.witness_id,
            )
        )

    for claim in report.failed_claims:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=SubjectRef("claim", f"{subject_id}:{claim.field}"),
                key=claim.reason,
                value=claim.field,
            )
        )

    for unknown in report.unknowns:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=SubjectRef("claim", f"{subject_id}:{unknown.field}"),
                key=f"unknown:{unknown.reason}",
                value=unknown.field,
            )
        )

    for area in report.unchecked_areas:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=SubjectRef("policy", area.area),
                key=f"unchecked:{area.reason}",
                value=area.area,
            )
        )

    for hazard in report.hazards:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=SubjectRef("draft", subject_id),
                key=f"hazard:{hazard.kind}",
                value=hazard.field or hazard.kind,
            )
        )

    for obligation in report.obligations:
        facts.add(
            Fact(
                tag="hazard_open",
                subject=SubjectRef("draft", subject_id),
                key=f"obligation:{obligation.kind}",
                value=obligation.field or obligation.kind,
            )
        )

    return facts
