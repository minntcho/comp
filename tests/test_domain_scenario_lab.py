import json

import pytest

from comp import DependencyFingerprint, ProjectionSpec
from tests.domain_scenarios.assertions import (
    assert_projection_tamper_blocked,
    assert_receipt_trace,
)
from tests.domain_scenarios.core import (
    ScenarioDefinition,
    ScenarioContract,
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
from tests.domain_scenarios.canonical_working_loop.scenario import (
    run_canonical_working_loop_scenario,
)
from tests.domain_scenarios.l_energy_pcf_governance.scenario import (
    run_l_energy_pcf_governance_scenario,
)
from tests.domain_scenarios.synthetic_pcf_anomaly.scenario import (
    run_synthetic_pcf_anomaly_scenario,
)
from tests.domain_scenarios.synthetic_pcf_smoke.scenario import (
    run_synthetic_pcf_smoke_scenario,
)


def test_domain_scenario_cli_lists_registered_scenarios(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "canonical_working_loop.raw_text_pcf.v1" in captured.out
    assert "tiny_pcf.location_based_electricity.v1" in captured.out
    assert "l_energy.alpha_invalid_allocation_rfi.v1" in captured.out
    assert "l_energy.alpha_physical_allocation_correction.v1" in captured.out
    assert "l_energy.steel_frame_proxy_assignment.v1" in captured.out
    assert "l_energy.carbon_tech_certificate_submission.v1" in captured.out
    assert "l_energy.l_materials_composition_rollup.v1" in captured.out
    assert "l_energy.c_pack_yield_rollup.v1" in captured.out
    assert "l_energy.tier0_physical_allocation.v1" in captured.out
    assert "l_energy.final_bottom_up_pcf_rollup.v1" in captured.out
    assert "l_energy_pcf_governance.v1" in captured.out
    assert "synthetic.raw_claim_hypothesis_gate.v1" in captured.out
    assert "synthetic_pcf.smoke.v1" in captured.out
    assert "synthetic_pcf.anomaly.v1" in captured.out
    assert "Canonical raw text PCF working loop" in captured.out


def test_domain_scenario_cli_runs_human_summary(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["run", "tiny_pcf.location_based_electricity.v1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Scenario: tiny_pcf.location_based_electricity.v1" in captured.out
    assert "Title: Tiny PCF location-based electricity" in captured.out
    assert "Status: accepted" in captured.out
    assert "Commit: commit" in captured.out
    assert "Projection: present" in captured.out
    assert "Resolver steps:" in captured.out
    assert "- deterministic_reference_selection" in captured.out
    assert "Receipt trace:" in captured.out
    assert "- reference bindings: 1" in captured.out
    assert "- derived claims: 1" in captured.out
    assert "Replay trace:" in captured.out
    assert "- status: replayed" in captured.out
    assert "- artifacts:" in captured.out


def test_domain_scenario_cli_runs_json_view(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["run", "tiny_pcf.location_based_electricity.v1", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"scenario_id": "tiny_pcf.location_based_electricity.v1"' in captured.out
    assert '"projection": {' in captured.out
    assert captured.err == ""


def test_domain_scenario_cli_rejects_unknown_scenario(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["run", "missing.scenario"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "unknown scenario id: missing.scenario" in captured.err
    assert "known scenarios:" in captured.err


def test_domain_scenario_cli_runs_all_registered_scenarios(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["run-all"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Domain Scenario Run" in captured.out
    assert "Passed: 14/14" in captured.out
    assert "- canonical_working_loop.raw_text_pcf.v1: pass" in captured.out
    assert "- tiny_pcf.location_based_electricity.v1: pass" in captured.out
    assert "- l_energy.alpha_invalid_allocation_rfi.v1: pass" in captured.out
    assert (
        "- l_energy.alpha_physical_allocation_correction.v1: pass"
        in captured.out
    )
    assert "- l_energy.steel_frame_proxy_assignment.v1: pass" in captured.out
    assert "- l_energy.carbon_tech_certificate_submission.v1: pass" in captured.out
    assert "- l_energy.l_materials_composition_rollup.v1: pass" in captured.out
    assert "- l_energy.c_pack_yield_rollup.v1: pass" in captured.out
    assert "- l_energy.tier0_physical_allocation.v1: pass" in captured.out
    assert "- l_energy.final_bottom_up_pcf_rollup.v1: pass" in captured.out
    assert "- l_energy_pcf_governance.v1: pass" in captured.out
    assert "- synthetic.raw_claim_hypothesis_gate.v1: pass" in captured.out
    assert "- synthetic_pcf.smoke.v1: pass" in captured.out
    assert "- synthetic_pcf.anomaly.v1: pass" in captured.out
    assert captured.err == ""


def test_domain_scenario_cli_runs_all_as_json(capsys):
    from tests.domain_scenarios.cli import main

    exit_code = main(["run-all", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["summary"] == {"total": 14, "passed": 14, "failed": 0}
    assert tuple(item["status"] for item in payload["scenarios"]) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert tuple(item["scenario_id"] for item in payload["scenarios"]) == (
        "canonical_working_loop.raw_text_pcf.v1",
        "tiny_pcf.location_based_electricity.v1",
        "l_energy.alpha_invalid_allocation_rfi.v1",
        "l_energy.alpha_physical_allocation_correction.v1",
        "l_energy.steel_frame_proxy_assignment.v1",
        "l_energy.carbon_tech_certificate_submission.v1",
        "l_energy.l_materials_composition_rollup.v1",
        "l_energy.c_pack_yield_rollup.v1",
        "l_energy.tier0_physical_allocation.v1",
        "l_energy.final_bottom_up_pcf_rollup.v1",
        "l_energy_pcf_governance.v1",
        "synthetic.raw_claim_hypothesis_gate.v1",
        "synthetic_pcf.smoke.v1",
        "synthetic_pcf.anomaly.v1",
    )
    assert "result" in payload["scenarios"][0]
    assert captured.err == ""


def test_domain_scenario_cli_run_all_reports_contract_failure(capsys, monkeypatch):
    from tests.domain_scenarios import cli

    failing_scenario = ScenarioDefinition(
        scenario_id="tiny_pcf.failure_fixture.v1",
        title="Tiny PCF failure fixture",
        run=run_tiny_pcf_scenario,
        contract=ScenarioContract(
            required_dependency_fingerprints=(
                DependencyFingerprint(
                    dependency_kind="compiler_profile",
                    dependency_id="missing-profile",
                    fingerprint="sha256:missing",
                ),
            )
        ),
    )
    monkeypatch.setattr(cli, "registered_scenarios", lambda: (failing_scenario,))

    exit_code = cli.main(["run-all"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Passed: 0/1" in captured.out
    assert "- tiny_pcf.failure_fixture.v1: fail" in captured.out
    assert captured.err == ""


def test_registered_scenarios_are_explicit_scenario_definitions():
    scenarios = registered_scenarios()

    assert tuple(scenario.scenario_id for scenario in scenarios) == (
        "canonical_working_loop.raw_text_pcf.v1",
        "tiny_pcf.location_based_electricity.v1",
        "l_energy.alpha_invalid_allocation_rfi.v1",
        "l_energy.alpha_physical_allocation_correction.v1",
        "l_energy.steel_frame_proxy_assignment.v1",
        "l_energy.carbon_tech_certificate_submission.v1",
        "l_energy.l_materials_composition_rollup.v1",
        "l_energy.c_pack_yield_rollup.v1",
        "l_energy.tier0_physical_allocation.v1",
        "l_energy.final_bottom_up_pcf_rollup.v1",
        "l_energy_pcf_governance.v1",
        "synthetic.raw_claim_hypothesis_gate.v1",
        "synthetic_pcf.smoke.v1",
        "synthetic_pcf.anomaly.v1",
    )
    assert all(isinstance(scenario, ScenarioDefinition) for scenario in scenarios)
    assert scenarios[1].contract.must_commit is True
    assert scenarios[1].contract.required_projection == EXPECTED_PROJECTION


def test_registered_scenarios_run_through_shared_contract_assertions():
    for scenario in registered_scenarios():
        result = run_scenario(scenario)

        assert_scenario_contract(result, scenario.contract)
        assert result.scenario_id == scenario.scenario_id


def test_scenario_contract_rejects_missing_dependency_fingerprint():
    result = run_l_energy_pcf_governance_scenario()
    contract = ScenarioContract(
        required_dependency_fingerprints=(
            DependencyFingerprint(
                dependency_kind="compiler_profile",
                dependency_id="missing-profile",
                fingerprint="sha256:missing",
            ),
        )
    )

    with pytest.raises(AssertionError):
        assert_scenario_contract(result, contract)


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


def test_synthetic_pcf_smoke_scenario_runs_generated_raw_to_receipt_flow():
    result = run_synthetic_pcf_smoke_scenario()

    assert result.scenario_id == "synthetic_pcf.smoke.v1"
    assert result.report.status == "accepted"
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == {
        "electricity_kwh": 1200,
        "co2e_kg": 504.0,
    }
    assert result.report.evidence_witnesses[0].source == (
        "raw_sources/erp_electricity.csv"
    )
    assert tuple(
        fingerprint.dependency_kind
        for fingerprint in result.preparation.receipt.citations.dependency_fingerprints
    ) == (
        "synthetic_manifest",
        "synthetic_source_input",
        "synthetic_source_input",
        "synthetic_source_input",
        "synthetic_source_input",
    )
    assert tuple(
        fingerprint.dependency_id
        for fingerprint in result.preparation.receipt.citations.dependency_fingerprints
        if fingerprint.dependency_kind == "synthetic_source_input"
    ) == (
        (
            "synthetic_source_input:synthetic_pcf.smoke.v1:"
            "seed-7:master_reference_catalog:reference_catalog.csv"
        ),
        (
            "synthetic_source_input:synthetic_pcf.smoke.v1:"
            "seed-7:master_sites:sites.csv"
        ),
        (
            "synthetic_source_input:synthetic_pcf.smoke.v1:"
            "seed-7:master_products:products.csv"
        ),
        (
            "synthetic_source_input:synthetic_pcf.smoke.v1:"
            "seed-7:raw_source:erp_electricity.csv"
        ),
    )


def test_synthetic_pcf_anomaly_scenario_blocks_generated_bad_rows():
    result = run_synthetic_pcf_anomaly_scenario()

    assert result.scenario_id == "synthetic_pcf.anomaly.v1"
    assert result.report.status == "blocked"
    assert result.preparation.decision.status == "hold"
    assert result.preparation.receipt is None
    assert result.projection is None
    assert tuple(result.preparation.package.open_obligation_ids) == (
        "synthetic-obligation:missing_unit",
        "synthetic-obligation:wrong_unit",
        "synthetic-obligation:period_mismatch",
        "synthetic-obligation:negative_amount",
        "synthetic-obligation:site_alias",
    )
    assert tuple(result.preparation.package.hazard_ids) == (
        "hazard:missing_unit:unit:review",
        "hazard:period_mismatch:period:review",
        "hazard:invalid_activity_amount:electricity_kwh:block",
        "hazard:site_alias:site_id:review",
    )
    assert tuple((claim.field, claim.reason) for claim in result.report.failed_claims) == (
        ("unit", "unsupported_unit"),
        ("electricity_kwh", "negative_amount"),
    )


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


def test_scenario_result_view_exposes_replay_trace_manifest_summary():
    result = run_canonical_working_loop_scenario()

    view = scenario_result_view(result)

    replay_trace = view["replay_trace"]
    assert replay_trace["status"] == "replayed"
    assert replay_trace["receipt_key"] == {
        "public_row_id": "public-row:canonical-raw-pcf-1",
        "projection_id": "canonical-pcf-public-row",
        "draft_id": "commit-package:product:canonical-raw-pcf-1",
    }
    assert {
        "artifact_id": "pcf-canonical-loop-v1",
        "artifact_kind": "compiler_profile",
    } in replay_trace["artifact_refs"]
    assert any(
        item["artifact_id"] == "canonical-raw:co2e_kg"
        and item["body_digest"].startswith("sha256:")
        for item in replay_trace["artifact_digests"]
    )
    assert replay_trace["dependency_manifests"]["profile_locks"] == [
        {
            "profile_id": "pcf-canonical-loop-v1",
            "active_rule_count": 0,
            "active_rubric_count": 0,
            "active_retrieval_policy_count": 1,
            "domain_pack_count": 1,
        }
    ]
    assert replay_trace["dependency_manifests"]["catalog_snapshots"] == [
        {
            "snapshot_id": (
                "reference_catalog_snapshot:"
                "pcf-reference-catalog:"
                "pcf-reference-catalog-v1"
            ),
            "catalog_id": "pcf-reference-catalog",
            "version": "pcf-reference-catalog-v1",
            "selected_record_count": 1,
        }
    ]
    assert "public_row" not in replay_trace
    assert "value" not in str(replay_trace["artifact_digests"])


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
