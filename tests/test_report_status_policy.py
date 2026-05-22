import pytest

from comp.compiler_tool import (
    ValidationReport,
    FailedClaim,
    Hazard,
    ValidationRequirement,
    UncheckedArea,
    UnknownClaim,
    recompute_report_status,
    with_recomputed_status,
)


@pytest.mark.parametrize(
    ("report", "expected_status"),
    (
        (
            ValidationReport(
                status="accepted",
                failed_claims=(
                    FailedClaim(
                        field="amount",
                        value="not a number",
                        reason="invalid_number",
                        origin="llm_inferred",
                    ),
                ),
            ),
            "blocked",
        ),
        (
            ValidationReport(
                status="accepted",
                obligations=(
                    ValidationRequirement(
                        kind="calculation_blocked",
                        field="co2e_emission",
                        reason="unit_mismatch",
                    ),
                ),
            ),
            "blocked",
        ),
        (
            ValidationReport(
                status="accepted",
                hazards=(Hazard(kind="conflict", field="scope2_method", severity="review"),),
            ),
            "review_required",
        ),
        (
            ValidationReport(
                status="accepted",
                obligations=(
                    ValidationRequirement(
                        kind="semantic_judgment_required",
                        field="scope2_method",
                        reason="semantic_support_required",
                    ),
                ),
            ),
            "review_required",
        ),
        (
            ValidationReport(
                status="accepted",
                unchecked_areas=(
                    UncheckedArea(field="factor_policy", reason="missing_rule_family"),
                ),
            ),
            "unchecked",
        ),
        (
            ValidationReport(
                status="accepted",
                unknowns=(UnknownClaim(field="period", reason="context_required"),),
            ),
            "underconstrained",
        ),
        (
            ValidationReport(
                status="accepted",
                obligations=(
                    ValidationRequirement(
                        kind="reference_selection_required",
                        field="co2e_emission",
                        reason="ambiguous",
                    ),
                ),
            ),
            "review_required",
        ),
        (
            ValidationReport(
                status="review_required",
                obligations=(
                    ValidationRequirement(
                        kind="nonblocking_hint",
                        field="co2e_emission",
                        reason="candidate_available",
                        blocking=False,
                    ),
                ),
            ),
            "accepted",
        ),
    ),
)
def test_recompute_report_status_uses_single_priority_policy(report, expected_status):
    assert recompute_report_status(report) == expected_status


def test_with_recomputed_status_preserves_report_payload():
    report = ValidationReport(
        status="accepted",
        hazards=(Hazard(kind="conflict", field="scope2_method", severity="review"),),
        can_build_public_output=True,
    )

    updated = with_recomputed_status(report)

    assert updated.status == "review_required"
    assert updated.hazards == report.hazards
    assert updated.can_build_public_output is True
