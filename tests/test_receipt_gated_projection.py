import pytest

from comp.judgment import CommitReceipt
from comp.projection import ProjectionBlocked, project_public_row


def test_projection_is_blocked_without_commit_receipt():
    with pytest.raises(ProjectionBlocked, match="CommitReceipt"):
        project_public_row(
            {"site": "SITE-SEOUL", "amount": 1200},
            output_fields=("site", "amount"),
            receipt=None,
        )


def test_projection_uses_commit_receipt_as_public_boundary():
    receipt = CommitReceipt(
        draft_id="draft-1",
        winner_receipt_ids=("selection-1",),
        barrier_snapshot=(("fresh", True),),
        public_row_id="row-1",
    )

    row = project_public_row(
        {"site": "SITE-SEOUL", "amount": 1200, "internal_note": "hidden"},
        output_fields=("site", "amount"),
        receipt=receipt,
    )

    assert row == {
        "public_row_id": "row-1",
        "draft_id": "draft-1",
        "site": "SITE-SEOUL",
        "amount": 1200,
    }
