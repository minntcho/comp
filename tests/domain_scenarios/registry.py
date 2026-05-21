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
from tests.domain_scenarios.l_energy_pcf_governance.tier0_physical_allocation import (
    TIER0_PHYSICAL_ALLOCATION_SCENARIO,
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
        L_ENERGY_PCF_GOVERNANCE_SCENARIO,
    )


__all__ = ["registered_scenarios"]
