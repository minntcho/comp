from comp.compiler_tool import (
    ClaimHypothesis,
    CompilerTool,
    Hazard,
    InterpretationHypothesis,
)


def test_unsupported_unit_claim_returns_blocked_report_with_obligation():
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-1",
        claims=(
            ClaimHypothesis(field="activity", value="electricity", witness_id="w-activity"),
            ClaimHypothesis(field="amount", value=1200, witness_id="w-amount"),
            ClaimHypothesis(field="unit", value="kWh"),
        ),
    )

    report = CompilerTool().compile_interpretation(hypothesis)

    assert report.status == "blocked"
    assert [claim.field for claim in report.passed_claims] == ["activity", "amount"]
    assert [(claim.field, claim.reason) for claim in report.failed_claims] == [
        ("unit", "missing_source_witness")
    ]
    assert [(obligation.kind, obligation.field) for obligation in report.obligations] == [
        ("find_source_witness", "unit")
    ]
    assert report.can_project_public_row is False


def test_missing_unit_hazard_returns_review_required_without_public_projection():
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-2",
        claims=(
            ClaimHypothesis(field="activity", value="electricity", witness_id="w-activity"),
            ClaimHypothesis(field="amount", value=1200, witness_id="w-amount"),
        ),
        hazards=(Hazard(kind="missing_unit", field="unit"),),
    )

    report = CompilerTool().compile_interpretation(hypothesis)

    assert report.status == "review_required"
    assert report.failed_claims == ()
    assert [(hazard.kind, hazard.field) for hazard in report.hazards] == [
        ("missing_unit", "unit")
    ]
    assert report.can_project_public_row is False
