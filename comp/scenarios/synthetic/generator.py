from __future__ import annotations

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    ExpectedArtifactRef,
    ExpectedClaim,
    ExpectedDependencyRef,
    ExpectedCalculatedClaim,
    ExpectedFailedClaim,
    ExpectedHazard,
    ExpectedValidationRequirement,
    ExpectedReceipt,
    ExpectedResolutionArtifact,
    ExpectedSourceMap,
    InjectedAnomaly,
    MasterReferenceRecord,
    OUTPUT_CONTRACT,
    RESOLUTION_OUTPUT_CONTRACT,
    SYNTHETIC_SOURCE_INPUT_KIND,
    RawElectricityRow,
    SyntheticInputBundle,
    SyntheticLoadedSource,
    SyntheticMaster,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticResolutionArtifact,
    SyntheticResolutionArtifacts,
    SyntheticRun,
)
from comp.scenarios.synthetic.run_builders import (
    build_synthetic_pcf_anomaly_run,
    build_synthetic_pcf_resolution_run,
    build_synthetic_pcf_smoke_run,
)
from comp.scenarios.synthetic.sources import (
    build_synthetic_loaded_source,
    build_synthetic_loaded_sources,
    synthetic_source_input_dependency_id,
)


def generate_synthetic_pcf_run(config: SyntheticScenarioConfig) -> SyntheticRun:
    if config.scenario_id == "synthetic_pcf.resolution.v1":
        return build_synthetic_pcf_resolution_run(config)
    if config.anomalies:
        return build_synthetic_pcf_anomaly_run(config)
    return build_synthetic_pcf_smoke_run(config)


__all__ = [
    "ExpectedClaim",
    "ExpectedCalculatedClaim",
    "ExpectedFailedClaim",
    "ExpectedHazard",
    "ExpectedValidationRequirement",
    "ExpectedArtifactRef",
    "ExpectedDependencyRef",
    "ExpectedReceipt",
    "ExpectedResolutionArtifact",
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "OUTPUT_CONTRACT",
    "RawElectricityRow",
    "RESOLUTION_OUTPUT_CONTRACT",
    "SYNTHETIC_SOURCE_INPUT_KIND",
    "SyntheticLoadedSource",
    "SyntheticInputBundle",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticRawSources",
    "SyntheticResolutionArtifact",
    "SyntheticResolutionArtifacts",
    "SyntheticRun",
    "build_synthetic_loaded_source",
    "build_synthetic_loaded_sources",
    "generate_synthetic_pcf_run",
    "synthetic_source_input_dependency_id",
]
