from __future__ import annotations

from typing import Any, Mapping

from comp.judgment import CommitReceipt


class ProjectionBlocked(ValueError):
    pass


def project_public_row(
    field_values: Mapping[str, Any],
    *,
    output_fields: tuple[str, ...],
    receipt: CommitReceipt | None,
) -> dict[str, Any]:
    if receipt is None:
        raise ProjectionBlocked("CommitReceipt is required for public projection")

    row = {
        "public_row_id": receipt.public_row_id,
        "draft_id": receipt.draft_id,
    }
    row.update({field: field_values.get(field) for field in output_fields})
    return row
