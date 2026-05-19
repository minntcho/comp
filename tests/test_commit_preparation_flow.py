import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    FailedClaim,
    ProofObligation,
    ReferenceBinding,
    prepare_commit,
)


def test_prepare_commit_builds_package_decision_and_receipt_for_accepted_report():
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

    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        profile_id="esg-ghg-v1",
        semantic_judgment_ids=("judgment-scope2",),
    )

    assert preparation.package.complete is True
    assert preparation.decision.status == "commit"
    assert preparation.receipt is not None
    assert preparation.can_project_public_row is True

    snapshot = dict(preparation.receipt.barrier_snapshot)
    assert snapshot["checked_claim_witness_ids"] == ("span-amount",)
    assert snapshot["semantic_judgment_ids"] == ("judgment-scope2",)
    assert snapshot["reference_binding_ids"] == ("bind-amount-factor",)
    assert snapshot["formula_ids"] == ("ghg.electricity_factor_multiplication.v1",)

    row = project_public_row(
        {"amount": 1200, "co2e_emission": 0.48, "internal_note": "hidden"},
        ProjectionSpec("public-row", ("amount", "co2e_emission")),
        receipt=preparation.receipt,
    )
    assert row == {"amount": 1200, "co2e_emission": 0.48}


def test_prepare_commit_returns_hold_without_receipt_for_open_obligations():
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

    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
    )

    assert preparation.package.open_obligation_ids == (
        "reference-selection:hyp-1:co2e_emission",
    )
    assert preparation.decision.status == "hold"
    assert preparation.receipt is None
    assert preparation.can_project_public_row is False
    with pytest.raises(ProjectionBlocked):
        project_public_row(
            {"co2e_emission": 0.48},
            ProjectionSpec("public-row", ("co2e_emission",)),
            receipt=preparation.receipt,
        )


def test_prepare_commit_returns_reject_without_receipt_for_terminal_failures():
    report = CompileReport(
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
    )

    assert preparation.package.report_status == "blocked"
    assert preparation.decision.status == "reject"
    assert preparation.receipt is None
