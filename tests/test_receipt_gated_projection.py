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
