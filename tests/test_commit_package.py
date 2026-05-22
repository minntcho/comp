from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    ValidationReport,
    CalculatedClaim,
    Hazard,
    ValidationRequirement,
    CanonicalReference,
    ReviewDecision,
    ReviewPackage,
    build_commit_package,
    decide_governance,
)


def test_commit_package_collects_report_artifacts_without_receipt_authority():
    report = ValidationReport(
        status="accepted",
        checked_claims=(
            CheckedClaim(
                field="amount",
                value=1200,
                witness_id="span-amount",
                origin="source_text",
            ),
        ),
        resolved_validation_requirements=(
            ValidationRequirement(
                kind="calculation_blocked",
                field="co2e_emission",
                reason="unknown_reference",
                obligation_id="calculation:hyp-1:co2e_emission",
            ),
        ),
        canonical_references=(
            CanonicalReference(
                binding_id="bind-amount-factor",
                claim_id="hyp-1:amount",
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
            ),
        ),
        calculated_claims=(
            CalculatedClaim(
                claim_id="hyp-1:co2e_emission",
                field="co2e_emission",
                value=0.48,
                unit="tCO2e",
                trace=CalculationTrace(
                    trace_id="trace:hyp-1:co2e_emission",
                    formula_id="ghg.electricity_factor_multiplication.v1",
                    input_claim_ids=("hyp-1:amount",),
                    reference_binding_ids=("bind-amount-factor",),
                ),
            ),
        ),
    )

    package = build_commit_package(
        report,
        subject_id="facility-1",
        profile_id="esg-ghg-v1",
        semantic_judgment_ids=("judgment-scope2",),
    )

    assert package.package_id == "commit-package:facility-1"
    assert package.subject_id == "facility-1"
    assert package.profile_id == "esg-ghg-v1"
    assert package.report_status == "accepted"
    assert package.checked_claim_fields == ("amount",)
    assert package.checked_claim_witness_ids == ("span-amount",)
    assert package.semantic_judgment_ids == ("judgment-scope2",)
    assert package.reference_binding_ids == ("bind-amount-factor",)
    assert package.derived_claim_ids == ("hyp-1:co2e_emission",)
    assert package.calculation_trace_ids == ("trace:hyp-1:co2e_emission",)
    assert package.formula_ids == ("ghg.electricity_factor_multiplication.v1",)
    assert package.open_obligation_ids == ()
    assert package.resolved_obligation_ids == ("calculation:hyp-1:co2e_emission",)
    assert package.hazard_ids == ()
    assert package.complete is True
    assert package.can_authorize_public_projection is False


def test_friendly_review_names_are_canonical():
    from comp.compiler_tool import ReviewPackage, ReviewDecision

    package = ReviewPackage(
        package_id="package-1",
        subject_id="facility-1",
        report_status="accepted",
        complete=True,
    )
    decision = decide_governance(package)

    assert type(package).__name__ == "ReviewPackage"
    assert type(decision).__name__ == "ReviewDecision"
    assert package.can_authorize_public_projection is False
    assert decision.can_authorize_public_projection is False
    assert decision.can_issue_commit_receipt is True


def test_commit_package_is_incomplete_with_open_blocking_obligation():
    report = ValidationReport(
        status="accepted",
        validation_requirements=(
            ValidationRequirement(
                kind="reference_selection_required",
                field="co2e_emission",
                reason="ambiguous",
                obligation_id="reference-selection:hyp-1:co2e_emission",
            ),
        ),
    )

    package = build_commit_package(report, subject_id="facility-1")

    assert package.report_status == "review_required"
    assert package.open_obligation_ids == (
        "reference-selection:hyp-1:co2e_emission",
    )
    assert package.complete is False


def test_commit_package_cites_nonblocking_obligations_without_blocking_completion():
    report = ValidationReport(
        status="review_required",
        validation_requirements=(
            ValidationRequirement(
                kind="nonblocking_hint",
                field="co2e_emission",
                reason="candidate_available",
                obligation_id="hint:hyp-1:co2e_emission",
                blocking=False,
            ),
        ),
    )

    package = build_commit_package(report, subject_id="facility-1")

    assert package.report_status == "accepted"
    assert package.open_obligation_ids == ("hint:hyp-1:co2e_emission",)
    assert package.complete is True


def test_commit_package_is_incomplete_with_hazards():
    report = ValidationReport(
        status="accepted",
        hazards=(Hazard(kind="conflict", field="scope2_method", severity="review"),),
    )

    package = build_commit_package(
        report,
        subject_id="facility-1",
        package_id="package-custom",
    )

    assert package.package_id == "package-custom"
    assert package.report_status == "review_required"
    assert package.hazard_ids == ("hazard:conflict:scope2_method:review",)
    assert package.complete is False
