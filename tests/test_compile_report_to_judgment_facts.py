from comp.compiler_tool import (
    CheckedClaim,
    ValidationReport,
    FailedClaim,
    Hazard,
    ValidationRequirement,
    UncheckedArea,
    UnknownClaim,
    add_compile_report_facts,
    compile_report_to_facts,
)
from comp.judgment import Fact, JudgmentState, SubjectRef


def test_compile_report_to_facts_maps_each_report_category():
    subject = SubjectRef("claim", "hyp-1")
    report = ValidationReport(
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
        validation_requirements=(
            ValidationRequirement(
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
        key="validation_requirement:unit",
        value="validation_requirement:find_source_witness:unit:unsupported_unit",
        meta=(
            ("kind", "find_source_witness"),
            ("reason", "unsupported_unit"),
            ("report_section", "validation_requirement"),
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


def test_resolved_validation_requirements_discharge_matching_hazard_ids():
    subject = SubjectRef("claim", "hyp-1")
    obligation = ValidationRequirement(
        kind="find_source_witness",
        field="unit",
        reason="unsupported_unit",
    )
    report = ValidationReport(status="accepted", resolved_validation_requirements=(obligation,))

    facts = compile_report_to_facts(report, subject)

    assert facts == {
        Fact(
            tag="hazard_discharge",
            subject=subject,
            key="validation_requirement:unit",
            value="validation_requirement:find_source_witness:unit:unsupported_unit",
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
                key="validation_requirement:unit",
                value="validation_requirement:find_source_witness:unit:unsupported_unit",
            )
        ]
    )

    add_compile_report_facts(state, report, subject)

    assert "validation_requirement:find_source_witness:unit:unsupported_unit" not in (
        state.active_hazard_ids(subject)
    )


def test_obligation_facts_preserve_explicit_obligation_ids():
    subject = SubjectRef("claim", "hyp-1")
    report = ValidationReport(
        status="review_required",
        validation_requirements=(
            ValidationRequirement(
                kind="semantic_judgment_required",
                field="scope2_method",
                reason="support_required",
                requirement_id="obl-custom-open",
            ),
        ),
        resolved_validation_requirements=(
            ValidationRequirement(
                kind="find_source_witness",
                field="unit",
                reason="unsupported_unit",
                requirement_id="obl-custom-resolved",
            ),
        ),
    )

    facts = compile_report_to_facts(report, subject)

    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="validation_requirement:scope2_method",
        value="obl-custom-open",
        meta=(
            ("kind", "semantic_judgment_required"),
            ("reason", "support_required"),
            ("report_section", "validation_requirement"),
            ("report_status", "review_required"),
        ),
    ) in facts
    assert Fact(
        tag="hazard_discharge",
        subject=subject,
        key="validation_requirement:unit",
        value="obl-custom-resolved",
        meta=(
            ("kind", "find_source_witness"),
            ("reason", "unsupported_unit"),
            ("report_section", "resolved_obligation"),
            ("report_status", "review_required"),
        ),
    ) in facts


def test_add_compile_report_facts_is_append_only_and_idempotent():
    subject = SubjectRef("claim", "hyp-1")
    report = ValidationReport(
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
