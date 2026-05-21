from comp import ProjectionSpec
from tests.domain_scenarios.assertions import assert_projection_tamper_blocked
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.registry import registered_scenarios
from tests.domain_scenarios.synthetic_pcf_resolution.scenario import (
    SCENARIO as SYNTHETIC_PCF_RESOLUTION_SCENARIO,
    run_synthetic_pcf_resolution_scenario,
)


def test_synthetic_pcf_resolution_scenario_commits_after_artifact_resolution():
    result = run_synthetic_pcf_resolution_scenario()

    assert result.scenario_id == "synthetic_pcf.resolution.v1"
    assert result.report.status == "accepted"
    assert result.report.obligations == ()
    assert result.report.hazards == ()
    assert result.preparation.decision.status == "commit"
    assert result.preparation.receipt is not None
    assert result.projection == {
        "electricity_kwh": 1200,
        "co2e_kg": 504.0,
    }
    assert (
        "synthetic-obligation:missing_unit"
        in result.preparation.package.resolved_obligation_ids
    )


def test_synthetic_pcf_resolution_receipt_blocks_tampered_projection():
    result = run_synthetic_pcf_resolution_scenario()

    assert_projection_tamper_blocked(
        result,
        ProjectionSpec(
            "synthetic-pcf-resolution-public-row",
            ("electricity_kwh", "co2e_kg"),
        ),
        {"co2e_kg": 999999},
    )


def test_synthetic_pcf_resolution_scenario_is_registered_with_contract():
    scenarios = registered_scenarios()

    assert "synthetic_pcf.resolution.v1" in tuple(
        scenario.scenario_id for scenario in scenarios
    )
    assert_scenario_contract(
        run_scenario(SYNTHETIC_PCF_RESOLUTION_SCENARIO),
        SYNTHETIC_PCF_RESOLUTION_SCENARIO.contract,
    )
