import pytest

import comp
from comp import CommitReceipt, ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import CompileReport


def test_accepted_compile_report_without_commit_receipt_cannot_project_public_row():
    report = CompileReport(status="accepted")
    projection = ProjectionSpec("public-row", ("site", "amount"))

    assert report.can_project_public_row is False
    with pytest.raises(ProjectionBlocked, match="CommitReceipt"):
        project_public_row({"site": "plant-a", "amount": 100}, projection)


def test_commit_receipt_allows_public_projection():
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
        ),
    )

    row = project_public_row(
        {"site": "plant-a", "amount": 100, "internal_note": "hidden"},
        projection,
        receipt=receipt,
    )

    assert row == {"site": "plant-a", "amount": 100}


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

    with pytest.raises(ProjectionBlocked, match="clean commit receipt"):
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

    with pytest.raises(ProjectionBlocked, match="clean commit receipt"):
        project_public_row({"site": "plant-a"}, projection, receipt=receipt)


def _clean_citations(
    *,
    projection_id,
    authorized_fields,
    checked_claim_fields,
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
    )
