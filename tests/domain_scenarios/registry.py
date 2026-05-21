from __future__ import annotations

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


def registered_scenarios() -> tuple[ScenarioDefinition, ...]:
    return (
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


__all__ = ["registered_scenarios"]
