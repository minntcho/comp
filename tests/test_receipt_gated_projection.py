import pytest

import comp
from comp import (
    PublicOutputBlocked,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputSpec,
    PublicOutputValueCommitment,
    build_public_output,
)
from comp.compiler_tool import ValidationReport


def test_accepted_compile_report_without_commit_receipt_cannot_build_public_output():
    report = ValidationReport(status="accepted")
    projection = PublicOutputSpec("public-row", ("site", "amount"))

    assert report.can_build_public_output is False
    with pytest.raises(PublicOutputBlocked, match="public-output receipt"):
        build_public_output({"site": "plant-a", "amount": 100}, projection)


def test_friendly_public_output_names_are_canonical():
    projection = PublicOutputSpec("public-row", ("site",))
    receipt = PublicOutputReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=PublicOutputReceiptCitations(
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

    assert type(projection).__name__ == "PublicOutputSpec"
    assert type(receipt).__name__ == "PublicOutputReceipt"
    assert type(receipt.citations).__name__ == "PublicOutputReceiptCitations"


def test_commit_receipt_allows_public_projection():
    projection = PublicOutputSpec("public-row", ("site", "amount"))
    commitments = (
        PublicOutputValueCommitment.from_value(
            field="site",
            source_kind="checked_claim",
            source_id="checked_claim:site:span-site",
            value="plant-a",
        ),
        PublicOutputValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:span-amount",
            value=100,
        ),
    )
    receipt = PublicOutputReceipt(
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

    row = build_public_output(
        {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
        projection,
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


def test_projection_rejects_tampered_committed_value():
    projection = PublicOutputSpec("public-row", ("site", "amount"))
    receipt = PublicOutputReceipt(
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
                PublicOutputValueCommitment.from_value(
                    field="site",
                    source_kind="checked_claim",
                    source_id="checked_claim:site:span-site",
                    value="plant-a",
                ),
                PublicOutputValueCommitment.from_value(
                    field="amount",
                    source_kind="checked_claim",
                    source_id="checked_claim:amount:span-amount",
                    value=100,
                ),
            ),
        ),
    )

    with pytest.raises(PublicOutputBlocked, match="value commitment"):
        build_public_output(
            {"site": "plant-a", "amount": 999999},
            projection,
            receipt=receipt,
        )


def test_projection_rejects_missing_committed_source_value():
    projection = PublicOutputSpec("public-row", ("site", "amount"))
    receipt = PublicOutputReceipt(
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
                PublicOutputValueCommitment.from_value(
                    field="site",
                    source_kind="checked_claim",
                    source_id="checked_claim:site:span-site",
                    value="plant-a",
                ),
                PublicOutputValueCommitment.from_value(
                    field="amount",
                    source_kind="checked_claim",
                    source_id="checked_claim:amount:span-amount",
                    value=100,
                ),
            ),
        ),
    )

    with pytest.raises(PublicOutputBlocked, match="missing committed value"):
        build_public_output({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_missing_value_commitment():
    projection = PublicOutputSpec("public-row", ("site",))
    receipt = PublicOutputReceipt(
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

    with pytest.raises(PublicOutputBlocked, match="value commitment"):
        build_public_output({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_duplicate_value_commitments():
    projection = PublicOutputSpec("public-row", ("site",))
    duplicate = PublicOutputValueCommitment.from_value(
        field="site",
        source_kind="checked_claim",
        source_id="checked_claim:site:span-site",
        value="plant-a",
    )
    receipt = PublicOutputReceipt(
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

    with pytest.raises(PublicOutputBlocked, match="duplicate value commitment"):
        build_public_output({"site": "plant-a"}, projection, receipt=receipt)


def test_top_level_projection_surface_is_receipt_gated():
    projection = PublicOutputSpec("public-row", ("site",))

    with pytest.raises(PublicOutputBlocked):
        comp.build_public_output({"site": "plant-a"}, projection)


def test_projection_rejects_receipt_without_citations():
    projection = PublicOutputSpec("public-row", ("site",))
    receipt = PublicOutputReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
    )

    with pytest.raises(PublicOutputBlocked, match="clean public-output receipt"):
        build_public_output({"site": "plant-a"}, projection, receipt=receipt)


def test_projection_rejects_receipt_with_unclean_citations():
    projection = PublicOutputSpec("public-row", ("site",))
    receipt = PublicOutputReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("active_hazards", ()),),
        public_row_id="public-row-1",
        projection_id="public-row",
        authorized_fields=("site",),
        citations=comp.PublicOutputReceiptCitations(
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

    with pytest.raises(PublicOutputBlocked, match="clean public-output receipt"):
        build_public_output({"site": "plant-a"}, projection, receipt=receipt)


def _clean_citations(
    *,
    projection_id,
    authorized_fields,
    checked_claim_fields,
    projection_value_commitments=(),
):
    return comp.PublicOutputReceiptCitations(
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
