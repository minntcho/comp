import pytest

import comp
from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    ProjectionBlocked,
    ProjectionSpec,
    ProjectionValueCommitment,
    PublicOutputBlocked,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputSpec,
    project_public_row,
)
from comp.compiler_tool import CompileReport


def test_accepted_compile_report_without_commit_receipt_cannot_project_public_row():
    report = CompileReport(status="accepted")
    projection = ProjectionSpec("public-row", ("site", "amount"))

    assert report.can_project_public_row is False
    with pytest.raises(PublicOutputBlocked, match="public-output receipt"):
        project_public_row({"site": "plant-a", "amount": 100}, projection)


def test_friendly_public_output_names_are_canonical_with_legacy_aliases():
    projection = ProjectionSpec("public-row", ("site",))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=CommitReceiptCitations(
            governance_decision_id="decision-1",
            governance_status="commit",
            governance_reasons=("commit_package_complete",),
            commit_package_id="package-1",
            commit_package_complete=True,
            subject_id="facility-1",
            projection_id="public-row",
            authorized_fields=("site",),
            profile_id=None,
            report_status="accepted",
            checked_claim_fields=("site",),
            checked_claim_witness_ids=("span-site",),
            semantic_judgment_ids=(),
            reference_binding_ids=(),
            derived_claim_fields=(),
            derived_claim_ids=(),
            calculation_trace_ids=(),
            formula_ids=(),
            resolved_obligation_ids=(),
            open_obligation_ids=(),
            hazard_ids=(),
        ),
    )

    assert ProjectionSpec is PublicOutputSpec
    assert ProjectionBlocked is PublicOutputBlocked
    assert CommitReceipt is PublicOutputReceipt
    assert CommitReceiptCitations is PublicOutputReceiptCitations
    assert type(projection).__name__ == "PublicOutputSpec"
    assert type(receipt).__name__ == "PublicOutputReceipt"
    assert type(receipt.citations).__name__ == "PublicOutputReceiptCitations"


def test_commit_receipt_allows_public_projection():
    projection = ProjectionSpec("public-row", ("site", "amount"))
    commitments = (
        ProjectionValueCommitment.from_value(
            field="site",
            source_kind="checked_claim",
            source_id="checked_claim:site:span-site",
            value="plant-a",
        ),
        ProjectionValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:span-amount",
            value=100,
        ),
    )
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=_clean_citations(
            projection_id="public-row",
            authorized_fields=("site", "amount"),
            checked_claim_fields=("site", "amount"),
            projection_value_commitments=commitments,
        ),
    )

    row = project_public_row(
        {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
        projection,
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


def test_projection_rejects_tampered_committed_value():
    projection = ProjectionSpec("public-row", ("site", "amount"))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=_clean_citations(
            projection_id="public-row",
            authorized_fields=("site", "amount"),
            checked_claim_fields=("site", "amount"),
            projection_value_commitments=(
                ProjectionValueCommitment.from_value(
                    field="site",
                    source_kind="checked_claim",
                    source_id="checked_claim:site:span-site",
                    value="plant-a",
                ),
                ProjectionValueCommitment.from_value(
                    field="amount",
                    source_kind="checked_claim",
                    source_id="checked_claim:amount:span-amount",
                    value=100,
                ),
            ),
        ),
    )

    with pytest.raises(ProjectionBlocked, match="value commitment"):
        project_public_row(
            {"site": "plant-a", "amount": 999999},
            projection,
            receipt=receipt,
        )


def test_projection_rejects_missing_committed_source_value():
    projection = ProjectionSpec("public-row", ("site", "amount"))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=_clean_citations(
            projection_id="public-row",
            authorized_fields=("site", "amount"),
            checked_claim_fields=("site", "amount"),
            projection_value_commitments=(
                ProjectionValueCommitment.from_value(
                    field="site",
                    source_kind="checked_claim",
                    source_id="checked_claim:site:span-site",
                    value="plant-a",
                ),
                ProjectionValueCommitment.from_value(
                    field="amount",
                    source_kind="checked_claim",
                    source_id="checked_claim:amount:span-amount",
                    value=100,
                ),
            ),
        ),
    )

    with pytest.raises(ProjectionBlocked, match="missing committed value"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_missing_value_commitment():
    projection = ProjectionSpec("public-row", ("site",))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=_clean_citations(
            projection_id="public-row",
            authorized_fields=("site",),
            checked_claim_fields=("site",),
            projection_value_commitments=(),
        ),
    )

    with pytest.raises(ProjectionBlocked, match="value commitment"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_duplicate_value_commitments():
    projection = ProjectionSpec("public-row", ("site",))
    duplicate = ProjectionValueCommitment.from_value(
        field="site",
        source_kind="checked_claim",
        source_id="checked_claim:site:span-site",
        value="plant-a",
    )
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=_clean_citations(
            projection_id="public-row",
            authorized_fields=("site",),
            checked_claim_fields=("site",),
            projection_value_commitments=(duplicate, duplicate),
        ),
    )

    with pytest.raises(ProjectionBlocked, match="duplicate value commitment"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def test_top_level_projection_surface_is_receipt_gated():
    projection = ProjectionSpec("public-row", ("site",))

    with pytest.raises(ProjectionBlocked):
        comp.project_public_row({"site": "plant-a"}, projection)


def test_projection_rejects_receipt_without_citations():
    projection = ProjectionSpec("public-row", ("site",))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
    )

    with pytest.raises(ProjectionBlocked, match="clean public-output receipt"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_receipt_with_unclean_citations():
    projection = ProjectionSpec("public-row", ("site",))
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=comp.CommitReceiptCitations(
            governance_decision_id="decision-1",
            governance_status="hold",
            governance_reasons=("open_obligation:obl-1",),
            commit_package_id="package-1",
            commit_package_complete=False,
            subject_id="facility-1",
            projection_id="public-row",
            authorized_fields=("site",),
            profile_id=None,
            report_status="review_required",
            checked_claim_fields=("site",),
            checked_claim_witness_ids=("span-site",),
            semantic_judgment_ids=(),
            reference_binding_ids=(),
            derived_claim_fields=(),
            derived_claim_ids=(),
            calculation_trace_ids=(),
            formula_ids=(),
            resolved_obligation_ids=(),
            open_obligation_ids=("obl-1",),
            hazard_ids=(),
        ),
    )

    with pytest.raises(ProjectionBlocked, match="clean public-output receipt"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def _clean_citations(
    *,
    projection_id,
    authorized_fields,
    checked_claim_fields,
    projection_value_commitments=(),
):
    return comp.CommitReceiptCitations(
        governance_decision_id="decision-1",
        governance_status="commit",
        governance_reasons=("commit_package_complete",),
        commit_package_id="package-1",
        commit_package_complete=True,
        subject_id="facility-1",
        projection_id=projection_id,
        authorized_fields=authorized_fields,
        profile_id=None,
        report_status="accepted",
        checked_claim_fields=checked_claim_fields,
        checked_claim_witness_ids=tuple(f"span-{field}" for field in checked_claim_fields),
        semantic_judgment_ids=(),
        reference_binding_ids=(),
        derived_claim_fields=(),
        derived_claim_ids=(),
        calculation_trace_ids=(),
        formula_ids=(),
        resolved_obligation_ids=(),
        open_obligation_ids=(),
        hazard_ids=(),
        projection_value_commitments=projection_value_commitments,
    )
