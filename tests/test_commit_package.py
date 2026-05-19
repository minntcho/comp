from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    Hazard,
    ProofObligation,
    ReferenceBinding,
    build_commit_package,
)


def test_commit_package_collects_report_artifacts_without_receipt_authority():
    report = CompileReport(
        status="accepted",
        checked_claims=(
            CheckedClaim(
                field="amount",
                value=1200,
                witness_id="span-amount",
                origin="source_text",
            ),
        ),
        resolved_obligations=(
            ProofObligation(
                kind="calculation_blocked",
                field="co2e_emission",
                reason="unknown_reference",
                obligation_id="calculation:hyp-1:co2e_emission",
            ),
        ),
        reference_bindings=(
            ReferenceBinding(
                binding_id="bind-amount-factor",
                claim_id="hyp-1:amount",
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
            ),
        ),
        derived_claims=(
            DerivedClaim(
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
    assert package.semantic_judgment_ids == ("judgment-scope2",)
    assert package.reference_binding_ids == ("bind-amount-factor",)
    assert package.derived_claim_ids == ("hyp-1:co2e_emission",)
    assert package.calculation_trace_ids == ("trace:hyp-1:co2e_emission",)
    assert package.open_obligation_ids == ()
    assert package.resolved_obligation_ids == ("calculation:hyp-1:co2e_emission",)
    assert package.hazard_ids == ()
    assert package.complete is True
    assert package.can_authorize_public_projection is False


def test_commit_package_is_incomplete_with_open_blocking_obligation():
    report = CompileReport(
        status="accepted",
        obligations=(
            ProofObligation(
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
    report = CompileReport(
        status="review_required",
        obligations=(
            ProofObligation(
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
    report = CompileReport(
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
