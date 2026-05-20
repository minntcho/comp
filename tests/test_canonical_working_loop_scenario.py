import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from tests.domain_scenarios.canonical_working_loop.fixtures import (
    RAW_EVIDENCE,
    compile_raw_evidence,
    extract_raw_evidence,
    open_calculation_obligation,
)
from tests.domain_scenarios.canonical_working_loop.scenario import (
    SCENARIO,
    run_canonical_working_loop_scenario,
)
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario


def test_canonical_working_loop_extracts_and_compiles_raw_text():
    hypothesis = extract_raw_evidence(RAW_EVIDENCE)

    assert hypothesis.subject_id == "product:canonical-raw-pcf-1"
    assert [(claim.field, claim.value) for claim in hypothesis.claims] == [
        ("activity", "electricity"),
        ("electricity_kwh", 1200),
        ("unit", "kWh"),
        ("reporting_year", 2024),
        ("geography", "KR"),
    ]
    assert all(witness.grounded for witness in hypothesis.witnesses)

    report = compile_raw_evidence(RAW_EVIDENCE)

    assert report.status == "accepted"
    assert [claim.field for claim in report.checked_claims] == [
        "activity",
        "electricity_kwh",
        "unit",
        "reporting_year",
        "geography",
    ]
    assert report.obligations == ()
    assert report.can_project_public_row is False


def test_canonical_working_loop_opens_calculation_obligation_after_compile():
    report = open_calculation_obligation(compile_raw_evidence(RAW_EVIDENCE))

    assert report.status == "blocked"
    assert [obligation.kind for obligation in report.obligations] == [
        "calculation_blocked",
    ]
    assert report.obligations[0].reason == "unknown_reference"
    assert report.derived_claims == ()


def test_canonical_working_loop_runs_raw_text_to_receipt_projection():
    result = run_scenario(SCENARIO)

    assert result.scenario_id == "canonical_working_loop.raw_text_pcf.v1"
    assert result.resolver_steps == (
        "raw_text_fixture",
        "deterministic_extractor_stub",
        "compiler_tool.compile_interpretation",
        "open_calculation_obligation",
        "plan_calculation_resolution",
        "resolver_tasks_from_report",
        "resolver_task_to_reference_query",
        "reference_retrieval:embedding_stub:factor",
        "deterministic_reference_selection",
        "retry_calculation",
        "prepare_commit",
        "receipt_gated_projection",
    )
    assert_scenario_contract(result, SCENARIO.contract)
    assert [
        candidate.retrieval_method for candidate in result.report.reference_candidates
    ] == [
        "embedding_stub:factor",
        "embedding_stub:factor",
    ]
    assert result.report.reference_bindings[0].selected_candidate_id == (
        "embedding_stub:factor:idx-canonical-kr-grid-2024"
    )
    assert result.projection == {
        "electricity_kwh": 1200,
        "reporting_year": 2024,
        "co2e_kg": 504.0,
    }


def test_canonical_working_loop_receipt_rejects_tampered_projection_value():
    result = run_canonical_working_loop_scenario()

    assert result.preparation.receipt is not None
    with pytest.raises(ProjectionBlocked, match="value commitment"):
        project_public_row(
            {
                "electricity_kwh": 1200,
                "reporting_year": 2024,
                "co2e_kg": 999999,
            },
            ProjectionSpec(
                "canonical-pcf-public-row",
                ("electricity_kwh", "reporting_year", "co2e_kg"),
            ),
            receipt=result.preparation.receipt,
        )
