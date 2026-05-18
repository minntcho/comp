from comp.compiler_tool import (
    ClaimHypothesis,
    CompileReport,
    CompilerTool,
    Hazard,
    InterpretationHypothesis,
    ProofObligation,
    UnknownClaim,
    UncheckedArea,
    compile_report_to_facts,
)
from comp.judgment import Fact, SubjectRef


def test_compile_report_emits_evidence_and_obligation_facts():
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-1",
        claims=(
            ClaimHypothesis(field="activity", value="electricity", witness_id="w-activity"),
            ClaimHypothesis(field="unit", value="kWh"),
        ),
    )
    report = CompilerTool().compile_interpretation(hypothesis)

    facts = compile_report_to_facts(report, subject_id=hypothesis.hypothesis_id)

    assert Fact(
        tag="evidence",
        subject=SubjectRef("claim", "hyp-1:activity"),
        key="activity",
        value="electricity",
        witness="w-activity",
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("claim", "hyp-1:unit"),
        key="missing_source_witness",
        value="unit",
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("draft", "hyp-1"),
        key="obligation:find_source_witness",
        value="unit",
    ) in facts


def test_compile_report_emits_unknown_unchecked_and_hazard_facts():
    report = CompileReport(
        status="underconstrained",
        unknowns=(UnknownClaim(field="period.year", reason="context_required"),),
        unchecked_areas=(UncheckedArea(area="factor_period_compatibility"),),
        hazards=(Hazard(kind="missing_unit", field="unit"),),
        obligations=(ProofObligation(kind="find_context", field="reporting_year"),),
    )

    facts = compile_report_to_facts(report, subject_id="hyp-2")

    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("claim", "hyp-2:period.year"),
        key="unknown:context_required",
        value="period.year",
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("policy", "factor_period_compatibility"),
        key="unchecked:missing_rule_coverage",
        value="factor_period_compatibility",
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("draft", "hyp-2"),
        key="hazard:missing_unit",
        value="unit",
    ) in facts
    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("draft", "hyp-2"),
        key="obligation:find_context",
        value="reporting_year",
    ) in facts
