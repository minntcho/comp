import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    ValidationReport,
    CalculatedClaim,
    FailedClaim,
    ValidationRequirement,
    CanonicalReference,
    prepare_commit,
)


def test_prepare_commit_builds_package_decision_and_receipt_for_accepted_report():
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

    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
        profile_id="esg-ghg-v1",
        semantic_judgment_ids=("judgment-scope2",),
    )

    assert preparation.package.complete is True
    assert preparation.decision.status == "commit"
    assert preparation.receipt is not None
    assert preparation.can_build_public_output is True

    snapshot = dict(preparation.receipt.barrier_snapshot)
    assert snapshot["checked_claim_witness_ids"] == ("span-amount",)
    assert snapshot["semantic_judgment_ids"] == ("judgment-scope2",)
    assert snapshot["reference_binding_ids"] == ("bind-amount-factor",)
    assert snapshot["derived_claim_fields"] == ("co2e_emission",)
    assert snapshot["formula_ids"] == ("ghg.electricity_factor_multiplication.v1",)
    assert preparation.receipt.projection_id == "public-row"
    assert preparation.receipt.authorized_fields == ("amount", "co2e_emission")

    row = build_public_output(
        {"amount": 1200, "co2e_emission": 0.48, "internal_note": "hidden"},
        PublicOutputSpec("public-row", ("amount", "co2e_emission")),
        receipt=preparation.receipt,
    )
    assert row == {"amount": 1200, "co2e_emission": 0.48}


def test_prepare_commit_returns_hold_without_receipt_for_open_obligations():
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

    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    assert preparation.package.open_obligation_ids == (
        "reference-selection:hyp-1:co2e_emission",
    )
    assert preparation.decision.status == "hold"
    assert preparation.receipt is None
    assert preparation.can_build_public_output is False
    with pytest.raises(PublicOutputBlocked):
        build_public_output(
            {"co2e_emission": 0.48},
            PublicOutputSpec("public-row", ("co2e_emission",)),
            receipt=preparation.receipt,
        )


def test_prepare_commit_returns_reject_without_receipt_for_terminal_failures():
    report = ValidationReport(
        status="accepted",
        failed_claims=(
            FailedClaim(
                field="amount",
                value="not a number",
                reason="invalid_number",
                origin="llm_inferred",
            ),
        ),
    )

    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    assert preparation.package.report_status == "blocked"
    assert preparation.decision.status == "reject"
    assert preparation.receipt is None
