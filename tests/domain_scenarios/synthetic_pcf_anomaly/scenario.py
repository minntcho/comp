from __future__ import annotations

from comp import SubjectRef
from comp.compiler_tool import prepare_commit
from comp.scenarios.synthetic import (
    SyntheticPcfAdapter,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
)
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)
from tests.domain_scenarios.synthetic_pcf_anomaly.expected import (
    EXPECTED_HAZARD_IDS,
    EXPECTED_OPEN_OBLIGATION_IDS,
)


SCENARIO_ID = "synthetic_pcf.anomaly.v1"
RESOLVER_STEPS = (
    "synthetic_scenario_generator",
    "raw_sources_only_adapter",
    "compiler_tool.compile_anomaly_pressure",
    "prepare_commit",
    "receipt_blocked_by_open_obligations",
)


SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic PCF anomaly pressure scenario",
    run=lambda: run_synthetic_pcf_anomaly_scenario(),
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=False,
        required_open_obligation_ids=EXPECTED_OPEN_OBLIGATION_IDS,
        required_hazard_ids=EXPECTED_HAZARD_IDS,
    ),
)


def run_synthetic_pcf_anomaly_scenario() -> DomainScenarioResult:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_anomaly(seed=11))
    adapter = SyntheticPcfAdapter(run.input_bundle)
    report = adapter.anomaly_report()
    preparation = prepare_commit(
        report,
        subject_id=adapter.subject_id,
        public_row_id=adapter.public_row_id,
        projection_id=adapter.projection_id,
        profile_id=adapter.profile_id,
        dependency_fingerprints=adapter.dependency_fingerprints(),
    )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=None,
        subject=SubjectRef("claim", adapter.subject_id),
        resolver_steps=RESOLVER_STEPS,
        external_material_source=adapter.external_material_source(),
    )


__all__ = ["SCENARIO", "run_synthetic_pcf_anomaly_scenario"]
