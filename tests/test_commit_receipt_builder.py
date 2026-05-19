import pytest

from comp import ProjectionSpec, project_public_row
from comp.compiler_tool import (
    CommitPackage,
    ReceiptBuildBlocked,
    build_commit_receipt,
    decide_governance,
)


def test_commit_receipt_builder_cites_package_and_governance_artifacts():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("amount",),
        checked_claim_witness_ids=("span-amount",),
        semantic_judgment_ids=("judgment-scope2",),
        reference_binding_ids=("bind-amount-factor",),
        derived_claim_ids=("hyp-1:co2e_emission",),
        calculation_trace_ids=("trace:hyp-1:co2e_emission",),
        formula_ids=("ghg.electricity_factor_multiplication.v1",),
        resolved_obligation_ids=("calculation:hyp-1:co2e_emission",),
        profile_id="esg-ghg-v1",
        complete=True,
    )
    decision = decide_governance(package)

    receipt = build_commit_receipt(
        package,
        decision,
        public_row_id="public-row-1",
    )

    snapshot = dict(receipt.barrier_snapshot)
    assert receipt.draft_id == "commit-package:facility-1"
    assert receipt.winner_receipt_ids == (
        "governance-decision:commit-package:facility-1",
    )
    assert receipt.public_row_id == "public-row-1"
    assert snapshot["governance_decision_id"] == decision.decision_id
    assert snapshot["governance_status"] == "commit"
    assert snapshot["commit_package_id"] == "commit-package:facility-1"
    assert snapshot["subject_id"] == "facility-1"
    assert snapshot["profile_id"] == "esg-ghg-v1"
    assert snapshot["checked_claim_fields"] == ("amount",)
    assert snapshot["checked_claim_witness_ids"] == ("span-amount",)
    assert snapshot["semantic_judgment_ids"] == ("judgment-scope2",)
    assert snapshot["reference_binding_ids"] == ("bind-amount-factor",)
    assert snapshot["derived_claim_ids"] == ("hyp-1:co2e_emission",)
    assert snapshot["calculation_trace_ids"] == ("trace:hyp-1:co2e_emission",)
    assert snapshot["formula_ids"] == ("ghg.electricity_factor_multiplication.v1",)
    assert snapshot["resolved_obligation_ids"] == (
        "calculation:hyp-1:co2e_emission",
    )
    assert snapshot["open_obligation_ids"] == ()
    assert snapshot["hazard_ids"] == ()


def test_generated_commit_receipt_can_authorize_existing_projection_gate():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        complete=True,
    )
    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
    )

    row = project_public_row(
        {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
        ProjectionSpec("public-row", ("site", "amount")),
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


def test_commit_receipt_builder_blocks_hold_decision():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="review_required",
        open_obligation_ids=("reference-selection:hyp-1:co2e_emission",),
        complete=False,
    )

    with pytest.raises(ReceiptBuildBlocked, match="commit decision"):
        build_commit_receipt(
            package,
            decide_governance(package),
            public_row_id="public-row-1",
        )


def test_commit_receipt_builder_blocks_package_mismatch():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        complete=True,
    )
    other_package = CommitPackage(
        package_id="commit-package:facility-2",
        subject_id="facility-2",
        report_status="accepted",
        complete=True,
    )

    with pytest.raises(ReceiptBuildBlocked, match="package mismatch"):
        build_commit_receipt(
            package,
            decide_governance(other_package),
            public_row_id="public-row-1",
        )
