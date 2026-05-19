from tests.domain_scenarios.tiny_pcf.scenario import run_tiny_pcf_scenario
from tests.domain_scenarios.tiny_pcf.expected import (
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_REJECTED_CANDIDATES,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
)


def test_tiny_pcf_scenario_runs_reference_to_receipt_flow():
    result = run_tiny_pcf_scenario()

    assert result.scenario_id == "tiny_pcf.location_based_electricity.v1"
    assert result.report.status == "accepted"
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == EXPECTED_PROJECTION


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
