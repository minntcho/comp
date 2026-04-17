from __future__ import annotations

import pytest

pytest.importorskip("lark")

from artifacts import DiagnosticArtifact
from tests.fixtures.cases import CASES
from tests.support.builders import run_pipeline_full, run_pipeline_until


def _case(name: str):
    return next(c for c in CASES if c.name == name)


def test_frame_diagnostics_are_diagnostic_artifacts():
    case = _case("aggregate_warning_calculation_excluded")
    result = run_pipeline_full(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
    )

    for frame in result.artifacts.frames:
        assert all(isinstance(d, DiagnosticArtifact) for d in frame.diagnostics)


def test_repair_populates_frame_runtime_state():
    case = _case("happy_path_merge_and_calculate")
    result = run_pipeline_until(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
        pass_name="RepairPass",
    )

    frame = result.artifacts.frames[0]
    assert frame.status == "committed"
    assert frame.runtime.iteration_count >= 1
    assert isinstance(frame.runtime.resolution_score, float)
    assert frame.runtime.termination_reason is not None


def test_row_error_codes_come_from_frame_diagnostics():
    case = _case("semantic_error_blocks_merge")
    result = run_pipeline_full(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
    )

    frame = result.artifacts.frames[0]
    row = result.artifacts.rows[0]
    frame_error_codes = sorted(
        d.code for d in frame.diagnostics if d.severity == "error"
    )

    assert row.error_codes == frame_error_codes
    assert result.artifacts.merge_log[0].action == "hold"
