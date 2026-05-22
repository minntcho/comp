from __future__ import annotations

from comp.scenarios.synthetic.anomaly_specs import (
    anomaly_specs,
    missing_unit_resolution_artifact,
    missing_unit_spec,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest
from comp.scenarios.synthetic.models import (
    OUTPUT_CONTRACT,
    RESOLUTION_OUTPUT_CONTRACT,
    SyntheticRawSources,
    SyntheticResolutionArtifacts,
    SyntheticRun,
)
from comp.scenarios.synthetic.oracle import (
    expected_anomaly_oracle,
    expected_resolution_oracle,
    expected_smoke_oracle,
)
from comp.scenarios.synthetic.pcf_fixtures import (
    pcf_master,
    raw_electricity_row,
)


def build_synthetic_pcf_smoke_run(config: SyntheticScenarioConfig) -> SyntheticRun:
    raw_row = raw_electricity_row(config)
    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        oracle=expected_smoke_oracle(config, raw_row),
    )


def build_synthetic_pcf_resolution_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    missing_unit = missing_unit_spec(config)
    raw_row = missing_unit.row
    resolution = missing_unit_resolution_artifact(raw_row)

    return SyntheticRun(
        config=config,
        manifest=build_manifest(
            config,
            output_contract=RESOLUTION_OUTPUT_CONTRACT,
        ),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        resolution_artifacts=SyntheticResolutionArtifacts(
            unit_witnesses=(resolution,),
        ),
        oracle=expected_resolution_oracle(config, missing_unit, resolution),
        output_contract=RESOLUTION_OUTPUT_CONTRACT,
    )


def build_synthetic_pcf_anomaly_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    specs = anomaly_specs(config)
    rows = tuple(spec.row for spec in specs)

    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=rows),
        oracle=expected_anomaly_oracle(specs),
    )

__all__ = [
    "build_synthetic_pcf_anomaly_run",
    "build_synthetic_pcf_resolution_run",
    "build_synthetic_pcf_smoke_run",
]
