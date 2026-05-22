import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    CommitPackage,
    CommitReceiptCitations,
    CompileReport,
    DerivedClaim,
    DependencyFingerprint,
    ProjectionValueCommitment,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    ReceiptBuildBlocked,
    build_commit_package,
    build_commit_receipt,
    build_public_output_receipt,
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
        derived_claim_fields=("co2e_emission",),
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
        projection_id="public-row",
    )

    snapshot = dict(receipt.barrier_snapshot)
    assert receipt.draft_id == "commit-package:facility-1"
    assert receipt.winner_receipt_ids == (
        "governance-decision:commit-package:facility-1",
    )
    assert receipt.public_row_id == "public-row-1"
    assert receipt.projection_id == "public-row"
    assert receipt.authorized_fields == ("amount", "co2e_emission")
    assert snapshot["governance_decision_id"] == decision.decision_id
    assert snapshot["governance_status"] == "commit"
    assert snapshot["commit_package_id"] == "commit-package:facility-1"
    assert snapshot["subject_id"] == "facility-1"
    assert snapshot["profile_id"] == "esg-ghg-v1"
    assert snapshot["checked_claim_fields"] == ("amount",)
    assert snapshot["checked_claim_witness_ids"] == ("span-amount",)
    assert snapshot["semantic_judgment_ids"] == ("judgment-scope2",)
    assert snapshot["reference_binding_ids"] == ("bind-amount-factor",)
    assert snapshot["derived_claim_fields"] == ("co2e_emission",)
    assert snapshot["derived_claim_ids"] == ("hyp-1:co2e_emission",)
    assert snapshot["calculation_trace_ids"] == ("trace:hyp-1:co2e_emission",)
    assert snapshot["formula_ids"] == ("ghg.electricity_factor_multiplication.v1",)
    assert snapshot["resolved_obligation_ids"] == (
        "calculation:hyp-1:co2e_emission",
    )
    assert snapshot["open_obligation_ids"] == ()
    assert snapshot["hazard_ids"] == ()


def test_friendly_receipt_builder_name_is_canonical_with_legacy_alias():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("amount",),
        checked_claim_witness_ids=("span-amount",),
        complete=True,
    )
    decision = decide_governance(package)

    receipt = build_public_output_receipt(
        package,
        decision,
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    assert build_commit_receipt is build_public_output_receipt
    assert isinstance(receipt, PublicOutputReceipt)
    assert isinstance(receipt.citations, PublicOutputReceiptCitations)
    assert CommitReceiptCitations is PublicOutputReceiptCitations
    assert type(receipt).__name__ == "PublicOutputReceipt"


def test_commit_receipt_builder_exposes_typed_citations():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("amount",),
        checked_claim_witness_ids=("span-amount",),
        semantic_judgment_ids=("judgment-scope2",),
        reference_binding_ids=("bind-amount-factor",),
        derived_claim_fields=("co2e_emission",),
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
        projection_id="public-row",
    )

    assert isinstance(receipt.citations, CommitReceiptCitations)
    assert receipt.citations.governance_decision_id == decision.decision_id
    assert receipt.citations.commit_package_id == "commit-package:facility-1"
    assert receipt.citations.subject_id == "facility-1"
    assert receipt.citations.profile_id == "esg-ghg-v1"
    assert receipt.citations.checked_claim_witness_ids == ("span-amount",)
    assert receipt.citations.semantic_judgment_ids == ("judgment-scope2",)
    assert receipt.citations.reference_binding_ids == ("bind-amount-factor",)
    assert receipt.citations.derived_claim_fields == ("co2e_emission",)
    assert receipt.citations.derived_claim_ids == ("hyp-1:co2e_emission",)
    assert receipt.citations.calculation_trace_ids == (
        "trace:hyp-1:co2e_emission",
    )
    assert receipt.citations.formula_ids == (
        "ghg.electricity_factor_multiplication.v1",
    )
    assert receipt.citations.to_barrier_snapshot() == receipt.barrier_snapshot


def test_commit_receipt_builder_cites_dependency_fingerprints():
    dependency = DependencyFingerprint(
        dependency_kind="compiler_profile",
        dependency_id="esg-ghg-v1",
        fingerprint="sha256:profile",
    )
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("amount",),
        checked_claim_witness_ids=("span-amount",),
        dependency_fingerprints=(dependency,),
        profile_id="esg-ghg-v1",
        complete=True,
    )
    decision = decide_governance(package)

    receipt = build_commit_receipt(
        package,
        decision,
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    assert receipt.citations is not None
    assert receipt.citations.dependency_fingerprints == (dependency,)
    assert dict(receipt.barrier_snapshot)["dependency_fingerprints"] == (
        dependency,
    )


def test_commit_receipt_builder_commits_checked_and_derived_projection_values():
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
        derived_claims=(
            DerivedClaim(
                claim_id="hyp-1:co2e_emission",
                field="co2e_emission",
                value=0.48,
                unit="tCO2e",
                trace=CalculationTrace(
                    trace_id="trace:hyp-1:co2e_emission",
                    formula_id="ghg.electricity_factor_multiplication.v1",
                ),
            ),
        ),
    )
    package = build_commit_package(
        report,
        subject_id="facility-1",
        profile_id="esg-ghg-v1",
    )

    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    commitments = receipt.citations.projection_value_commitments
    assert commitments == (
        ProjectionValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:span-amount",
            value=1200,
        ),
        ProjectionValueCommitment.from_value(
            field="co2e_emission",
            source_kind="derived_claim",
            source_id="hyp-1:co2e_emission",
            value=0.48,
        ),
    )

    snapshot = dict(receipt.barrier_snapshot)
    assert snapshot["projection_value_commitments"] == commitments
    assert tuple(ProjectionValueCommitment.__dataclass_fields__) == (
        "field",
        "source_kind",
        "source_id",
        "value_digest",
        "digest_alg",
    )
    assert all(commitment.value_digest.startswith("sha256:") for commitment in commitments)


def test_commit_receipt_value_digests_preserve_value_type():
    report = CompileReport(
        status="accepted",
        checked_claims=(
            CheckedClaim(
                field="amount_int",
                value=1200,
                witness_id="span-int",
                origin="source_text",
            ),
            CheckedClaim(
                field="amount_int_again",
                value=1200,
                witness_id="span-int-again",
                origin="source_text",
            ),
            CheckedClaim(
                field="amount_str",
                value="1200",
                witness_id="span-str",
                origin="source_text",
            ),
            CheckedClaim(
                field="amount_float",
                value=1200.0,
                witness_id="span-float",
                origin="source_text",
            ),
        ),
    )
    package = build_commit_package(report, subject_id="facility-1")
    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    commitments = {
        commitment.field: commitment
        for commitment in receipt.citations.projection_value_commitments
    }

    assert commitments["amount_int"].value_digest.startswith("sha256:")
    assert (
        commitments["amount_int"].value_digest
        == commitments["amount_int_again"].value_digest
    )
    assert (
        commitments["amount_int"].value_digest
        != commitments["amount_str"].value_digest
    )
    assert (
        commitments["amount_int"].value_digest
        != commitments["amount_float"].value_digest
    )


def test_generated_commit_receipt_can_authorize_existing_projection_gate():
    report = CompileReport(
        status="accepted",
        checked_claims=(
            CheckedClaim(
                field="site",
                value="plant-a",
                witness_id="span-site",
                origin="source_text",
            ),
            CheckedClaim(
                field="amount",
                value=100,
                witness_id="span-amount",
                origin="source_text",
            ),
        ),
    )
    package = build_commit_package(report, subject_id="facility-1")
    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    row = project_public_row(
        {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
        ProjectionSpec("public-row", ("site", "amount")),
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


def test_commit_receipt_cannot_authorize_different_projection():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("site", "amount"),
        complete=True,
    )
    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    with pytest.raises(ProjectionBlocked, match="authorize this public output"):
        project_public_row(
            {"site": "plant-a", "amount": 100},
            ProjectionSpec("audit-row", ("site", "amount")),
            receipt=receipt,
        )


def test_commit_receipt_cannot_authorize_unscoped_projection_fields():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("site", "amount"),
        complete=True,
    )
    receipt = build_commit_receipt(
        package,
        decide_governance(package),
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    with pytest.raises(ProjectionBlocked, match="unauthorized field"):
        project_public_row(
            {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
            ProjectionSpec("public-row", ("site", "internal_note")),
            receipt=receipt,
        )


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
            projection_id="public-row",
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
            projection_id="public-row",
        )
