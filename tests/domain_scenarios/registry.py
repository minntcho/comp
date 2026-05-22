from __future__ import annotations

from dataclasses import dataclass

from tests.domain_scenarios.core import ScenarioDefinition
from tests.domain_scenarios.canonical_working_loop.scenario import (
    SCENARIO as CANONICAL_WORKING_LOOP_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.scenario import (
    SCENARIO as L_ENERGY_PCF_GOVERNANCE_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.alpha_invalid_allocation_rfi import (
    ALPHA_INVALID_ALLOCATION_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.alpha_physical_allocation_correction import (
    ALPHA_PHYSICAL_ALLOCATION_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.c_pack_yield_rollup import (
    C_PACK_YIELD_ROLLUP_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.carbon_tech_certificate_submission import (
    CARBON_TECH_CERTIFICATE_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.l_materials_composition_rollup import (
    L_MATERIALS_COMPOSITION_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.steel_frame_proxy_assignment import (
    STEEL_FRAME_PROXY_SCENARIO,
)
from tests.domain_scenarios.synthetic_pcf_anomaly.scenario import (
    SCENARIO as SYNTHETIC_PCF_ANOMALY_SCENARIO,
)
from tests.domain_scenarios.synthetic_pcf_resolution.scenario import (
    SCENARIO as SYNTHETIC_PCF_RESOLUTION_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.tier0_physical_allocation import (
    TIER0_PHYSICAL_ALLOCATION_SCENARIO,
)
from tests.domain_scenarios.l_energy_pcf_governance.final_bottom_up_rollup import (
    FINAL_BOTTOM_UP_ROLLUP_SCENARIO,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_gate.scenario import (
    RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_acceptance.scenario import (
    RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO,
)
from tests.domain_scenarios.synthetic_raw_claim_conflict.scenario import (
    RAW_CLAIM_CONFLICT_SCENARIO,
)
from tests.domain_scenarios.synthetic_raw_claim_conflict_resolution.scenario import (
    RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO,
)
from tests.domain_scenarios.synthetic_pcf_smoke.scenario import (
    SCENARIO as SYNTHETIC_PCF_SMOKE_SCENARIO,
)
from tests.domain_scenarios.tiny_pcf.scenario import SCENARIO as TINY_PCF_SCENARIO


@dataclass(frozen=True)
class ScenarioResidency:
    tier: str
    reason: str
    target_pack: str | None = None
    external_pack_id: str | None = None
    external_contract_id: str | None = None
    cutover_state: str = "internal-kernel-regression"


_REGISTERED_SCENARIOS = (
    CANONICAL_WORKING_LOOP_SCENARIO,
    TINY_PCF_SCENARIO,
    ALPHA_INVALID_ALLOCATION_SCENARIO,
    ALPHA_PHYSICAL_ALLOCATION_SCENARIO,
    STEEL_FRAME_PROXY_SCENARIO,
    CARBON_TECH_CERTIFICATE_SCENARIO,
    L_MATERIALS_COMPOSITION_SCENARIO,
    C_PACK_YIELD_ROLLUP_SCENARIO,
    TIER0_PHYSICAL_ALLOCATION_SCENARIO,
    FINAL_BOTTOM_UP_ROLLUP_SCENARIO,
    L_ENERGY_PCF_GOVERNANCE_SCENARIO,
    RAW_CLAIM_HYPOTHESIS_GATE_SCENARIO,
    RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO,
    RAW_CLAIM_CONFLICT_SCENARIO,
    RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO,
    SYNTHETIC_PCF_SMOKE_SCENARIO,
    SYNTHETIC_PCF_ANOMALY_SCENARIO,
    SYNTHETIC_PCF_RESOLUTION_SCENARIO,
)
_LARGE_DOMAIN_DOWNSTREAM_IDS = frozenset(
    scenario.scenario_id
    for scenario in (
        ALPHA_INVALID_ALLOCATION_SCENARIO,
        ALPHA_PHYSICAL_ALLOCATION_SCENARIO,
        STEEL_FRAME_PROXY_SCENARIO,
        CARBON_TECH_CERTIFICATE_SCENARIO,
        L_MATERIALS_COMPOSITION_SCENARIO,
        C_PACK_YIELD_ROLLUP_SCENARIO,
        TIER0_PHYSICAL_ALLOCATION_SCENARIO,
        FINAL_BOTTOM_UP_ROLLUP_SCENARIO,
        L_ENERGY_PCF_GOVERNANCE_SCENARIO,
    )
)
_SYNTHETIC_PCF_DOWNSTREAM_IDS = frozenset(
    scenario.scenario_id
    for scenario in (
        SYNTHETIC_PCF_SMOKE_SCENARIO,
        SYNTHETIC_PCF_ANOMALY_SCENARIO,
        SYNTHETIC_PCF_RESOLUTION_SCENARIO,
    )
)
_DOWNSTREAM_CANDIDATE_IDS = (
    _LARGE_DOMAIN_DOWNSTREAM_IDS | _SYNTHETIC_PCF_DOWNSTREAM_IDS
)
_ROLLUP_EXTERNAL_PACK_IDS = {
    STEEL_FRAME_PROXY_SCENARIO.scenario_id: (
        "l_energy_steel_frame_proxy_assignment"
    ),
    CARBON_TECH_CERTIFICATE_SCENARIO.scenario_id: (
        "l_energy_carbon_tech_certificate_submission"
    ),
    L_MATERIALS_COMPOSITION_SCENARIO.scenario_id: (
        "l_energy_l_materials_composition_rollup"
    ),
    C_PACK_YIELD_ROLLUP_SCENARIO.scenario_id: "l_energy_c_pack_yield_rollup",
    TIER0_PHYSICAL_ALLOCATION_SCENARIO.scenario_id: (
        "l_energy_tier0_physical_allocation"
    ),
    FINAL_BOTTOM_UP_ROLLUP_SCENARIO.scenario_id: (
        "l_energy_final_bottom_up_pcf_rollup"
    ),
}


def _scenario_residency_for(scenario_id: str) -> ScenarioResidency:
    if scenario_id == ALPHA_INVALID_ALLOCATION_SCENARIO.scenario_id:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            external_pack_id="l_energy_alpha_invalid_allocation_rfi",
            external_contract_id="canonical_blocked_projection_smoke",
            cutover_state="parallel-validation",
            reason=(
                "blocked large domain workflow fixture has a seeded downstream "
                "canonical bundle but remains internal until parallel validation "
                "covers the same trust meaning"
            ),
        )
    if scenario_id == ALPHA_PHYSICAL_ALLOCATION_SCENARIO.scenario_id:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            external_pack_id="l_energy_alpha_physical_allocation_correction",
            external_contract_id="canonical_projection_smoke",
            cutover_state="parallel-validation",
            reason=(
                "accepted large domain workflow fixture has a seeded downstream "
                "canonical bundle but remains internal until parallel validation "
                "covers the same trust meaning"
            ),
        )
    if scenario_id in _ROLLUP_EXTERNAL_PACK_IDS:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            external_pack_id=_ROLLUP_EXTERNAL_PACK_IDS[scenario_id],
            external_contract_id="canonical_projection_smoke",
            cutover_state="parallel-validation",
            reason=(
                "accepted large domain workflow rollup-chain fixture has a seeded "
                "downstream canonical bundle but remains internal until "
                "parallel validation covers the same trust meaning"
            ),
        )
    if scenario_id == L_ENERGY_PCF_GOVERNANCE_SCENARIO.scenario_id:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            external_pack_id="l_energy_pcf_governance",
            external_contract_id="canonical_projection_smoke",
            cutover_state="parallel-validation",
            reason=(
                "large domain workflow fixture has a seeded downstream canonical "
                "bundle but remains internal until parallel validation covers the "
                "same trust meaning"
            ),
        )
    if scenario_id in _LARGE_DOMAIN_DOWNSTREAM_IDS:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            cutover_state="pending-external-coverage",
            reason=(
                "large domain workflow fixture retained temporarily until the "
                "downstream scenario pack owns it"
            ),
        )
    if scenario_id in _SYNTHETIC_PCF_DOWNSTREAM_IDS:
        return ScenarioResidency(
            tier="downstream-candidate",
            target_pack="comp-scenario-packs",
            cutover_state="pending-external-coverage",
            reason=(
                "synthetic generator fixture retained temporarily until the "
                "downstream scenario pack owns generated replay checks"
            ),
        )
    return ScenarioResidency(
        tier="core-kernel",
        cutover_state="internal-kernel-regression",
        reason="small authority boundary scenario for comp kernel regression",
    )


_SCENARIO_RESIDENCY = {
    scenario.scenario_id: _scenario_residency_for(scenario.scenario_id)
    for scenario in _REGISTERED_SCENARIOS
}


def registered_scenarios() -> tuple[ScenarioDefinition, ...]:
    return _REGISTERED_SCENARIOS


def core_kernel_scenarios() -> tuple[ScenarioDefinition, ...]:
    return tuple(
        scenario
        for scenario in _REGISTERED_SCENARIOS
        if _SCENARIO_RESIDENCY[scenario.scenario_id].tier == "core-kernel"
    )


def downstream_candidate_scenarios() -> tuple[ScenarioDefinition, ...]:
    return tuple(
        scenario
        for scenario in _REGISTERED_SCENARIOS
        if _SCENARIO_RESIDENCY[scenario.scenario_id].tier == "downstream-candidate"
    )


def scenario_residency(scenario_id: str) -> ScenarioResidency:
    return _SCENARIO_RESIDENCY[scenario_id]


__all__ = [
    "ScenarioResidency",
    "core_kernel_scenarios",
    "downstream_candidate_scenarios",
    "registered_scenarios",
    "scenario_residency",
]
