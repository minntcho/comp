from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row


def assert_projection_tamper_blocked(
    result,
    projection: ProjectionSpec,
    overrides: Mapping[str, Any],
    *,
    match: str = "value commitment",
) -> None:
    if result.projection is None:
        raise AssertionError("scenario result has no projection to tamper")
    if result.preparation.receipt is None:
        raise AssertionError("scenario result has no receipt to enforce projection")

    tampered_values = dict(result.projection)
    tampered_values.update(overrides)

    with pytest.raises(ProjectionBlocked, match=match):
        project_public_row(
            tampered_values,
            projection,
            receipt=result.preparation.receipt,
        )


def assert_receipt_trace(
    result,
    *,
    reference_binding_ids: tuple[str, ...] | None = None,
    derived_claim_ids: tuple[str, ...] | None = None,
    calculation_trace_ids: tuple[str, ...] | None = None,
    formula_ids: tuple[str, ...] | None = None,
) -> None:
    if result.preparation.receipt is None:
        raise AssertionError("scenario result has no receipt")
    if result.preparation.receipt.citations is None:
        raise AssertionError("scenario receipt has no citations")

    citations = result.preparation.receipt.citations
    if reference_binding_ids is not None:
        assert citations.reference_binding_ids == reference_binding_ids
    if derived_claim_ids is not None:
        assert citations.derived_claim_ids == derived_claim_ids
    if calculation_trace_ids is not None:
        assert citations.calculation_trace_ids == calculation_trace_ids
    if formula_ids is not None:
        assert citations.formula_ids == formula_ids


__all__ = [
    "assert_projection_tamper_blocked",
    "assert_receipt_trace",
]
