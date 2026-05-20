from __future__ import annotations

from tests.domain_scenarios.core import ScenarioDefinition
from tests.domain_scenarios.l_energy_pcf_governance.scenario import (
    SCENARIO as L_ENERGY_PCF_GOVERNANCE_SCENARIO,
)
from tests.domain_scenarios.tiny_pcf.scenario import SCENARIO as TINY_PCF_SCENARIO


def registered_scenarios() -> tuple[ScenarioDefinition, ...]:
    return (TINY_PCF_SCENARIO, L_ENERGY_PCF_GOVERNANCE_SCENARIO)


__all__ = ["registered_scenarios"]
