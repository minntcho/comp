import pytest

from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CompileReport,
    DerivedClaim,
    ProofObligation,
    SemanticJudgment,
    SemanticJudgmentRequirement,
    apply_semantic_judgments,
    compile_report_to_facts,
)
from comp.judgment import Fact, SubjectRef


def _trace():
    return CalculationTrace(
        trace_id="trace-electricity-co2e",
        formula_id="ghg.electricity_factor_multiplication.v1",
        input_claim_ids=("hyp-1:amount",),
        reference_binding_ids=("bind-amount-factor",),
        steps=(
            CalculationStep(
                step_id="multiply-activity-by-factor",
                operation="multiply",
                input_ids=("hyp-1:amount", "bind-amount-factor"),
                output_value=0.48,
                output_unit="tCO2e",
            ),
        ),
    )


def _derived_claim():
    return DerivedClaim(
        claim_id="hyp-1:co2e_emission",
        field="co2e_emission",
        value=0.48,
        unit="tCO2e",
        trace=_trace(),
    )


def test_derived_claim_is_calculated_claim_not_public_authority():
    claim = _derived_claim()

    assert claim.origin == "calculated"
    assert claim.formula_id == "ghg.electricity_factor_multiplication.v1"
    assert claim.can_authorize_public_projection is False

    report = CompileReport(status="accepted", derived_claims=(claim,))

    assert report.derived_claims == (claim,)
    assert report.can_project_public_row is False


def test_calculation_trace_requires_formula_id():
    with pytest.raises(ValueError, match="formula_id"):
        CalculationTrace(
            trace_id="trace-1",
            formula_id="",
            input_claim_ids=("hyp-1:amount",),
        )


def test_semantic_judgment_application_preserves_derived_claims():
    claim = _derived_claim()
    obligation = ProofObligation(
        kind="semantic_judgment_required",
        field="scope2_method",
        reason="semantic_support_required",
        obligation_id="obl-scope2",
        semantic_requirement=SemanticJudgmentRequirement(
            question="Does the span support market-based Scope 2?",
            claim_id="hyp-1:scope2_method",
            evidence_span_ids=("span-17",),
            rubric_id="ghg.scope2_method.v1",
            acceptable_verdicts=("supports", "refutes", "ambiguous"),
        ),
    )
    report = CompileReport(
        status="review_required",
        obligations=(obligation,),
        derived_claims=(claim,),
    )

    updated = apply_semantic_judgments(
        report,
        [
            SemanticJudgment(
                judgment_id="judgment-1",
                obligation_id="obl-scope2",
                verdict="supports",
                rubric_id="ghg.scope2_method.v1",
                judge="llm/test",
                cited_span_ids=("span-17",),
                rationale="Fixture judgment.",
            )
        ],
        available_span_ids=("span-17",),
    )

    assert updated.derived_claims == (claim,)


def test_compile_report_to_facts_maps_derived_claim_with_trace_metadata():
    subject = SubjectRef("claim", "hyp-1")
    claim = _derived_claim()
    report = CompileReport(status="accepted", derived_claims=(claim,))

    facts = compile_report_to_facts(report, subject)

    assert Fact(
        tag="evidence",
        subject=subject,
        key="co2e_emission",
        value=0.48,
        witness="trace-electricity-co2e",
        weight=1.0,
        meta=(
            ("claim_id", "hyp-1:co2e_emission"),
            ("formula_id", "ghg.electricity_factor_multiplication.v1"),
            ("input_claim_ids", ("hyp-1:amount",)),
            ("origin", "calculated"),
            ("reference_binding_ids", ("bind-amount-factor",)),
            ("report_section", "derived_claim"),
            ("report_status", "accepted"),
            ("trace_id", "trace-electricity-co2e"),
            ("unit", "tCO2e"),
        ),
    ) in facts
