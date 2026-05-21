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
from tests.domain_scenarios.tiny_pcf.scenario import SCENARIO as TINY_PCF_SCENARIO


def registered_scenarios() -> tuple[ScenarioDefinition, ...]:
    return (
        CANONICAL_WORKING_LOOP_SCENARIO,
        TINY_PCF_SCENARIO,
        ALPHA_INVALID_ALLOCATION_SCENARIO,
        L_ENERGY_PCF_GOVERNANCE_SCENARIO,
    )


__all__ = ["registered_scenarios"]
