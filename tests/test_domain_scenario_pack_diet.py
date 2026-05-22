from pathlib import Path

from tests.domain_scenarios.registry import (
    core_kernel_scenarios,
    downstream_candidate_scenarios,
    registered_scenarios,
    scenario_residency,
)


def test_domain_scenario_registry_marks_core_and_downstream_candidate_sets():
    registered_ids = {scenario.scenario_id for scenario in registered_scenarios()}
    core_ids = {scenario.scenario_id for scenario in core_kernel_scenarios()}
    downstream_ids = {
        scenario.scenario_id for scenario in downstream_candidate_scenarios()
    }

    assert core_ids | downstream_ids == registered_ids
    assert core_ids.isdisjoint(downstream_ids)
    assert core_ids == {
        "canonical_working_loop.raw_text_pcf.v1",
        "tiny_pcf.location_based_electricity.v1",
        "synthetic.raw_claim_hypothesis_gate.v1",
        "synthetic.raw_claim_hypothesis_acceptance.v1",
        "synthetic.raw_claim_conflict.v1",
        "synthetic.raw_claim_conflict_resolution.v1",
    }
    assert downstream_ids == {
        "l_energy.alpha_invalid_allocation_rfi.v1",
        "l_energy.alpha_physical_allocation_correction.v1",
        "l_energy.steel_frame_proxy_assignment.v1",
        "l_energy.carbon_tech_certificate_submission.v1",
        "l_energy.l_materials_composition_rollup.v1",
        "l_energy.c_pack_yield_rollup.v1",
        "l_energy.tier0_physical_allocation.v1",
        "l_energy.final_bottom_up_pcf_rollup.v1",
        "l_energy_pcf_governance.v1",
        "synthetic_pcf.smoke.v1",
        "synthetic_pcf.anomaly.v1",
        "synthetic_pcf.resolution.v1",
    }


def test_domain_scenario_residency_metadata_explains_diet_boundary():
    raw_claim_residency = scenario_residency(
        "synthetic.raw_claim_conflict_resolution.v1"
    )
    l_energy_residency = scenario_residency("l_energy.final_bottom_up_pcf_rollup.v1")
    synthetic_residency = scenario_residency("synthetic_pcf.smoke.v1")

    assert raw_claim_residency.tier == "core-kernel"
    assert raw_claim_residency.target_pack is None
    assert "authority boundary" in raw_claim_residency.reason

    assert l_energy_residency.tier == "downstream-candidate"
    assert l_energy_residency.target_pack == "comp-scenario-packs"
    assert "large domain workflow" in l_energy_residency.reason

    assert synthetic_residency.tier == "downstream-candidate"
    assert synthetic_residency.target_pack == "comp-scenario-packs"
    assert "synthetic generator" in synthetic_residency.reason


def test_domain_scenario_docs_explain_residency_tiers():
    readme = Path("tests/domain_scenarios/README.md").read_text(encoding="utf-8")
    extension_doc = Path("docs/extensions/scenario-packs.md").read_text(
        encoding="utf-8"
    )

    assert "Scenario Residency" in readme
    assert "core-kernel" in readme
    assert "downstream-candidate" in readme
    assert "l_energy.*" in readme
    assert "synthetic PCF smoke/anomaly/resolution" in readme
    assert "copy/reconstruct -> external run -> parallel validation" in extension_doc
    assert "public_projection_smoke" in extension_doc
    assert "registry exposes residency metadata" in extension_doc
