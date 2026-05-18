from comp.compiler_tool import (
    CheckedClaim,
    CompileReport,
    FailedClaim,
    Hazard,
    ProofObligation,
    UncheckedArea,
    UnknownClaim,
    add_compile_report_facts,
    compile_report_to_facts,
)
from comp.judgment import Fact, JudgmentState, SubjectRef


def test_compile_report_to_facts_maps_each_report_category():
    subject = SubjectRef("claim", "hyp-1")
    report = CompileReport(
        status="blocked",
        checked_claims=(
            CheckedClaim(
                field="amount",
                value=100,
                witness_id="w-amount",
                origin="llm_inferred",
            ),
        ),
        failed_claims=(
            FailedClaim(
                field="unit",
                value="mwh",
                reason="unsupported_unit",
                origin="llm_inferred",
                witness_id="w-unit",
            ),
        ),
        unknowns=(UnknownClaim(field="reporting_year", reason="context_required"),),
        unchecked_areas=(
            UncheckedArea(
                field="factor_period_compatibility",
                reason="missing_rule_coverage",
            ),
        ),
        obligations=(
            ProofObligation(
                kind="find_source_witness",
                field="unit",
                reason="unsupported_unit",
            ),
        ),
        hazards=(Hazard(kind="missing_unit", field="unit", severity="review"),),
    )

    facts = compile_report_to_facts(report, subject)

    assert Fact(
        tag="evidence",
        subject=subject,
        key="amount",
        value=100,
        witness="w-amount",
        weight=1.0,
        meta=(
            ("origin", "llm_inferred"),
            ("report_section", "checked_claim"),
            ("report_status", "blocked"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="failed_claim:unit",
        value="failed_claim:unit:unsupported_unit",
        witness="w-unit",
        meta=(
            ("origin", "llm_inferred"),
            ("reason", "unsupported_unit"),
            ("report_section", "failed_claim"),
            ("report_status", "blocked"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="unknown_claim:reporting_year",
        value="unknown_claim:reporting_year:context_required",
        meta=(
            ("reason", "context_required"),
            ("report_section", "unknown_claim"),
            ("report_status", "blocked"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="unchecked_area:factor_period_compatibility",
        value="unchecked_area:factor_period_compatibility:missing_rule_coverage",
        meta=(
            ("reason", "missing_rule_coverage"),
            ("report_section", "unchecked_area"),
            ("report_status", "blocked"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="proof_obligation:unit",
        value="proof_obligation:find_source_witness:unit:unsupported_unit",
        meta=(
            ("kind", "find_source_witness"),
            ("reason", "unsupported_unit"),
            ("report_section", "proof_obligation"),
            ("report_status", "blocked"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="hazard:unit",
        value="hazard:missing_unit:unit:review",
        meta=(
            ("kind", "missing_unit"),
            ("report_section", "hazard"),
            ("report_status", "blocked"),
            ("severity", "review"),
        ),
    ) in facts
    assert not any(
        fact.tag == "evidence" and fact.key == "factor_period_compatibility"
        for fact in facts
    )


def test_resolved_obligations_discharge_matching_hazard_ids():
    subject = SubjectRef("claim", "hyp-1")
    obligation = ProofObligation(
        kind="find_source_witness",
        field="unit",
        reason="unsupported_unit",
    )
    report = CompileReport(status="accepted", resolved_obligations=(obligation,))

    facts = compile_report_to_facts(report, subject)

    assert facts == {
        Fact(
            tag="hazard_discharge",
            subject=subject,
            key="proof_obligation:unit",
            value="proof_obligation:find_source_witness:unit:unsupported_unit",
            meta=(
                ("kind", "find_source_witness"),
                ("reason", "unsupported_unit"),
                ("report_section", "resolved_obligation"),
                ("report_status", "accepted"),
            ),
        )
    }
    state = JudgmentState()
    state.add_facts(
        [
            Fact(
                tag="hazard_open",
                subject=subject,
                key="proof_obligation:unit",
                value="proof_obligation:find_source_witness:unit:unsupported_unit",
            )
        ]
    )

    add_compile_report_facts(state, report, subject)

    assert "proof_obligation:find_source_witness:unit:unsupported_unit" not in (
        state.active_hazard_ids(subject)
    )


def test_add_compile_report_facts_is_append_only_and_idempotent():
    subject = SubjectRef("claim", "hyp-1")
    report = CompileReport(
        status="accepted",
        checked_claims=(
            CheckedClaim(
                field="unit",
                value="kwh",
                witness_id="w-unit",
                origin="source_text",
            ),
        ),
    )
    state = JudgmentState()

    first_delta = add_compile_report_facts(state, report, subject)
    second_delta = add_compile_report_facts(state, report, subject)

    assert first_delta == compile_report_to_facts(report, subject)
    assert second_delta == set()
    assert state.version_of(subject) == 1
