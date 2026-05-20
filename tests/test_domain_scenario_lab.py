from comp import ProjectionSpec
from tests.domain_scenarios.assertions import (
    assert_projection_tamper_blocked,
    assert_receipt_trace,
)
from tests.domain_scenarios.core import (
    ScenarioDefinition,
    SourceRef,
    assert_scenario_contract,
    run_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.views import scenario_result_view
from tests.domain_scenarios.tiny_pcf.expected import (
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_REJECTED_CANDIDATES,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
)
from tests.domain_scenarios.tiny_pcf.scenario import run_tiny_pcf_scenario


def test_registered_scenarios_are_explicit_scenario_definitions():
    scenarios = registered_scenarios()

    assert tuple(scenario.scenario_id for scenario in scenarios) == (
        "canonical_working_loop.raw_text_pcf.v1",
        "tiny_pcf.location_based_electricity.v1",
        "l_energy_pcf_governance.v1",
    )
    assert all(isinstance(scenario, ScenarioDefinition) for scenario in scenarios)
    assert scenarios[1].contract.must_commit is True
    assert scenarios[1].contract.required_projection == EXPECTED_PROJECTION


def test_registered_scenarios_run_through_shared_contract_assertions():
    for scenario in registered_scenarios():
        result = run_scenario(scenario)

        assert_scenario_contract(result, scenario.contract)
        assert result.scenario_id == scenario.scenario_id


def test_source_ref_serializes_external_scenario_trace_metadata():
    source = SourceRef(
        repo="minntcho/esg-platform",
        commit="618c44dfcea1ee1e235550776acb78d8f20a7e0c",
        path="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
    )

    assert source.to_dict() == {
        "repo": "minntcho/esg-platform",
        "commit": "618c44dfcea1ee1e235550776acb78d8f20a7e0c",
        "path": "tests/e2e/cases/001-l-energy-pcf-governance.yaml",
    }


def test_tiny_pcf_scenario_runs_reference_to_receipt_flow():
    result = run_tiny_pcf_scenario()

    assert result.scenario_id == "tiny_pcf.location_based_electricity.v1"
    assert result.report.status == "accepted"
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION


def test_tiny_pcf_scenario_rejects_tampered_projection_value():
    result = run_tiny_pcf_scenario()

    assert_projection_tamper_blocked(
        result,
        ProjectionSpec("pcf-public-row", ("electricity_kwh", "co2e_kg")),
        {"co2e_kg": 999999},
        match="value commitment",
    )


def test_tiny_pcf_scenario_preserves_traceable_domain_artifacts():
    result = run_tiny_pcf_scenario()

    assert tuple(item.kind for item in result.report.resolved_obligations) == (
        EXPECTED_RESOLVED_OBLIGATION_KINDS
    )
    assert tuple(
        candidate.reference_id for candidate in result.report.reference_candidates
    ) == EXPECTED_REFERENCE_CANDIDATE_IDS

    binding = result.report.reference_bindings[0]
    assert binding.reference_id == "pcf.factor.kr_grid_2024.location_based"
    assert binding.selected_candidate_id == (
        "keyword:pcf.factor.kr_grid_2024.location_based"
    )
    assert tuple(
        (item.reference_id, item.reason) for item in binding.rejected_candidates
    ) == EXPECTED_REJECTED_CANDIDATES

    derived = result.report.derived_claims[0]
    assert derived.claim_id == "tiny-pcf:co2e_kg"
    assert derived.value == 504.0
    assert derived.trace.reference_binding_ids == ("bind-electricity-factor",)

    assert_receipt_trace(
        result,
        reference_binding_ids=("bind-electricity-factor",),
        derived_claim_ids=("tiny-pcf:co2e_kg",),
        calculation_trace_ids=("trace:tiny-pcf:co2e_kg",),
        formula_ids=("pcf.electricity_factor_multiplication.v1",),
    )


def test_scenario_result_view_exposes_receipt_trace_without_raw_values():
    result = run_tiny_pcf_scenario()

    view = scenario_result_view(result)

    assert view == result.to_dict()
    assert view["receipt_trace"]["reference_binding_ids"] == (
        "bind-electricity-factor",
    )
    assert view["receipt_trace"]["derived_claim_ids"] == ("tiny-pcf:co2e_kg",)
    assert view["receipt_trace"]["calculation_trace_ids"] == (
        "trace:tiny-pcf:co2e_kg",
    )
    assert view["receipt_trace"]["formula_ids"] == (
        "pcf.electricity_factor_multiplication.v1",
    )

    commitments = view["receipt_trace"]["value_commitments"]
    assert commitments == [
        {
            "field": "electricity_kwh",
            "source_kind": "checked_claim",
            "source_id": "checked_claim:electricity_kwh:span-electricity-amount",
            "value_digest": (
                "sha256:"
                "7aa3fcfca9c3b08fbec22b363aa33f2f23d6dbecf3cb935c06c6900cb24d91bb"
            ),
            "digest_alg": "sha256",
        },
        {
            "field": "co2e_kg",
            "source_kind": "derived_claim",
            "source_id": "tiny-pcf:co2e_kg",
            "value_digest": (
                "sha256:"
                "042ee367826ac0a5248c3e060dbd2466bd9e44a5f11d5ba2dcab18417e888a9b"
            ),
            "digest_alg": "sha256",
        },
    ]
    assert all("value" not in commitment for commitment in commitments)


def test_tiny_pcf_scenario_exports_json_ready_viewer_payload():
    exported = run_tiny_pcf_scenario().to_dict()

    assert exported["scenario_id"] == "tiny_pcf.location_based_electricity.v1"
    assert exported["report"]["status"] == "accepted"
    assert exported["report"]["reference_bindings"] == [
        {
            "binding_id": "bind-electricity-factor",
            "reference_id": "pcf.factor.kr_grid_2024.location_based",
            "selected_candidate_id": "keyword:pcf.factor.kr_grid_2024.location_based",
            "rejected_candidates": [
                {
                    "reference_id": "pcf.factor.kr_grid_2023.location_based",
                    "reason": "attribute_mismatch:valid_period",
                }
            ],
        }
    ]
    assert exported["commit"]["governance_status"] == "commit"
    assert exported["commit"]["receipt_id"] == "public-row:tiny-pcf-1"
    assert exported["projection"] == EXPECTED_PROJECTION
