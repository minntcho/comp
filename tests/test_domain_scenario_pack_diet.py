import json
from pathlib import Path

from tests.domain_scenarios.registry import (
    core_kernel_scenarios,
    downstream_candidate_scenarios,
    registered_scenarios,
    scenario_residency,
)

ROLLUP_EXTERNAL_PACKS = {
    "l_energy.steel_frame_proxy_assignment.v1": (
        "l_energy_steel_frame_proxy_assignment"
    ),
    "l_energy.carbon_tech_certificate_submission.v1": (
        "l_energy_carbon_tech_certificate_submission"
    ),
    "l_energy.l_materials_composition_rollup.v1": (
        "l_energy_l_materials_composition_rollup"
    ),
    "l_energy.c_pack_yield_rollup.v1": "l_energy_c_pack_yield_rollup",
    "l_energy.tier0_physical_allocation.v1": (
        "l_energy_tier0_physical_allocation"
    ),
    "l_energy.final_bottom_up_pcf_rollup.v1": (
        "l_energy_final_bottom_up_pcf_rollup"
    ),
}

SYNTHETIC_PCF_EXTERNAL_PACKS = {
    "synthetic_pcf.smoke.v1": (
        "synthetic_pcf_smoke",
        "canonical_projection_smoke",
    ),
    "synthetic_pcf.anomaly.v1": (
        "synthetic_pcf_anomaly",
        "canonical_blocked_projection_smoke",
    ),
    "synthetic_pcf.resolution.v1": (
        "synthetic_pcf_resolution",
        "canonical_projection_smoke",
    ),
}


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


def test_downstream_candidate_cutover_metadata_tracks_external_coverage():
    l_energy = scenario_residency("l_energy_pcf_governance.v1")
    blocked_allocation = scenario_residency(
        "l_energy.alpha_invalid_allocation_rfi.v1"
    )
    accepted_allocation = scenario_residency(
        "l_energy.alpha_physical_allocation_correction.v1"
    )
    rollup_residencies = {
        scenario_id: scenario_residency(scenario_id)
        for scenario_id in ROLLUP_EXTERNAL_PACKS
    }
    synthetic_residencies = {
        scenario_id: scenario_residency(scenario_id)
        for scenario_id in SYNTHETIC_PCF_EXTERNAL_PACKS
    }
    raw_claim = scenario_residency(
        "synthetic.raw_claim_conflict_resolution.v1"
    )

    assert l_energy.tier == "downstream-candidate"
    assert l_energy.target_pack == "comp-scenario-packs"
    assert l_energy.external_pack_id == "l_energy_pcf_governance"
    assert l_energy.external_contract_id == "canonical_projection_smoke"
    assert l_energy.cutover_state == "parallel-validation"

    assert blocked_allocation.tier == "downstream-candidate"
    assert blocked_allocation.target_pack == "comp-scenario-packs"
    assert blocked_allocation.external_pack_id == (
        "l_energy_alpha_invalid_allocation_rfi"
    )
    assert blocked_allocation.external_contract_id == (
        "canonical_blocked_projection_smoke"
    )
    assert blocked_allocation.cutover_state == "parallel-validation"

    assert accepted_allocation.tier == "downstream-candidate"
    assert accepted_allocation.target_pack == "comp-scenario-packs"
    assert accepted_allocation.external_pack_id == (
        "l_energy_alpha_physical_allocation_correction"
    )
    assert accepted_allocation.external_contract_id == "canonical_projection_smoke"
    assert accepted_allocation.cutover_state == "parallel-validation"

    for scenario_id, external_pack_id in ROLLUP_EXTERNAL_PACKS.items():
        residency = rollup_residencies[scenario_id]
        assert residency.tier == "downstream-candidate"
        assert residency.target_pack == "comp-scenario-packs"
        assert residency.external_pack_id == external_pack_id
        assert residency.external_contract_id == "canonical_projection_smoke"
        assert residency.cutover_state == "parallel-validation"

    for scenario_id, (
        external_pack_id,
        external_contract_id,
    ) in SYNTHETIC_PCF_EXTERNAL_PACKS.items():
        residency = synthetic_residencies[scenario_id]
        assert residency.tier == "downstream-candidate"
        assert residency.target_pack == "comp-scenario-packs"
        assert residency.external_pack_id == external_pack_id
        assert residency.external_contract_id == external_contract_id
        assert residency.cutover_state == "parallel-validation"

    assert raw_claim.tier == "core-kernel"
    assert raw_claim.cutover_state == "internal-kernel-regression"


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
    assert "Cutover states" in readme
    assert "internal-kernel-regression" in readme
    assert "pending-external-coverage" in readme
    assert "parallel-validation" in readme
    assert "copy/reconstruct -> external run -> parallel validation" in extension_doc
    assert "public_projection_smoke" in extension_doc
    assert "l_energy_alpha_invalid_allocation_rfi" in extension_doc
    assert "l_energy_alpha_physical_allocation_correction" in extension_doc
    for external_pack_id in ROLLUP_EXTERNAL_PACKS.values():
        assert external_pack_id in extension_doc
    for external_pack_id, _contract_id in SYNTHETIC_PCF_EXTERNAL_PACKS.values():
        assert external_pack_id in extension_doc
    assert "registry exposes residency metadata" in extension_doc
    assert "Scenario replay uses the production materializer boundary" in readme
    assert "materialize_compiler_run_artifacts(...)" in readme
    assert "ExternalArtifactMaterialSource" in readme
    assert "fixture-owned external material" in readme
    assert "not construct\n`ArtifactEnvelope` objects directly" in readme


def test_domain_scenario_replay_uses_production_materializer_boundary():
    source = Path("tests/domain_scenarios/persistence.py").read_text(
        encoding="utf-8"
    )

    assert "materialize_compiler_run_artifacts" in source
    assert "build_receipt_envelope_set" in source
    assert "_scenario_external_material_source" in source
    assert "external_material_source=" in source

    for stale_policy in (
        "ArtifactEnvelope.from_body(",
        "receipt_artifact_refs(",
        "evidence_ref_fingerprint",
        "_artifact_envelope_for_ref",
        "_artifact_body_for_ref",
        "_scenario_external_artifact_bodies",
        "dependency_artifact_bodies",
        "external_artifact_bodies=",
    ):
        assert stale_policy not in source


def test_downstream_registry_records_active_pack_cutover_state():
    registry = json.loads(
        Path("docs/extensions/downstream-registry.json").read_text(
            encoding="utf-8"
        )
    )
    packs = {pack["id"]: pack for pack in registry["packs"]}
    downstream = packs["comp-scenario-packs"]

    assert downstream["status"] == "active"
    assert downstream["authority_policy"] == (
        "compatibility_signal_not_authority_source"
    )
    assert downstream["dependency_direction"] == "downstream_consumes_comp"
    assert downstream["required_for_comp_pr_ci"] is False
    assert downstream["recommended_for_release_candidate"] is True
    assert downstream["current_packs"] == [
        {
            "id": "public_projection_smoke",
            "status": "active",
            "scope": "canonical-runtime-smoke",
            "cutover_state": "baseline-public-surface",
            "covers_comp_scenario_ids": [],
        },
        {
            "id": "l_energy_alpha_invalid_allocation_rfi",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.alpha_invalid_allocation_rfi.v1"
            ],
        },
        {
            "id": "l_energy_alpha_physical_allocation_correction",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.alpha_physical_allocation_correction.v1"
            ],
        },
        {
            "id": "l_energy_c_pack_yield_rollup",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.c_pack_yield_rollup.v1"
            ],
        },
        {
            "id": "l_energy_carbon_tech_certificate_submission",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.carbon_tech_certificate_submission.v1"
            ],
        },
        {
            "id": "l_energy_final_bottom_up_pcf_rollup",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.final_bottom_up_pcf_rollup.v1"
            ],
        },
        {
            "id": "l_energy_l_materials_composition_rollup",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.l_materials_composition_rollup.v1"
            ],
        },
        {
            "id": "l_energy_pcf_governance",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": ["l_energy_pcf_governance.v1"],
        },
        {
            "id": "l_energy_steel_frame_proxy_assignment",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.steel_frame_proxy_assignment.v1"
            ],
        },
        {
            "id": "l_energy_tier0_physical_allocation",
            "status": "seed",
            "scope": "large-domain-and-product-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": [
                "l_energy.tier0_physical_allocation.v1"
            ],
        },
        {
            "id": "synthetic_pcf_anomaly",
            "status": "seed",
            "scope": "synthetic-generator-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": ["synthetic_pcf.anomaly.v1"],
        },
        {
            "id": "synthetic_pcf_resolution",
            "status": "seed",
            "scope": "synthetic-generator-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": ["synthetic_pcf.resolution.v1"],
        },
        {
            "id": "synthetic_pcf_smoke",
            "status": "seed",
            "scope": "synthetic-generator-e2e",
            "cutover_state": "parallel-validation",
            "covers_comp_scenario_ids": ["synthetic_pcf.smoke.v1"],
        },
    ]


def test_downstream_registry_records_machine_readable_boundary_policy():
    registry = json.loads(
        Path("docs/extensions/downstream-registry.json").read_text(
            encoding="utf-8"
        )
    )
    boundary_policy = registry["boundary_policy"]
    extension_doc = Path("docs/extensions/scenario-packs.md").read_text(
        encoding="utf-8"
    )

    assert boundary_policy["comp_owns"] == [
        "authority_contracts",
        "receipts",
        "projection_gates",
        "replay_validation",
        "minimal_kernel_e2e_scenarios",
    ]
    assert boundary_policy["downstream_owns"] == [
        "large_domain_workflows",
        "product_platform_fixtures",
        "importers",
        "ui_viewer_flows",
        "supplier_workflows",
    ]
    assert boundary_policy["comp_must_not"] == [
        "clone_downstream_repositories_for_pr_ci",
        "use_git_submodules_for_scenario_packs",
        "import_downstream_scenario_code_in_production",
        "require_large_downstream_scenarios_before_v1",
    ]
    assert boundary_policy["cutover_sequence"] == [
        "copy_or_reconstruct",
        "external_run",
        "parallel_validation",
        "internal_shrink_or_remove",
    ]

    for phrase in (
        "Machine-readable boundary policy",
        "comp_owns",
        "downstream_owns",
        "comp_must_not",
        "cutover_sequence",
    ):
        assert phrase in extension_doc
