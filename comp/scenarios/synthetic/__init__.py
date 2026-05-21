"""Synthetic scenario generator for comp tests.

This package produces raw inputs and oracle expectations. It does not validate
claims, issue receipts, or authorize public projection.
"""

from comp.scenarios.synthetic.adapters import SyntheticPcfAdapter
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.generator import (
    ExpectedArtifactRef,
    ExpectedClaim,
    ExpectedDependencyRef,
    ExpectedDerivedClaim,
    ExpectedFailedClaim,
    ExpectedHazard,
    ExpectedObligation,
    ExpectedReceipt,
    ExpectedResolutionArtifact,
    ExpectedSourceMap,
    InjectedAnomaly,
    MasterReferenceRecord,
    RawElectricityRow,
    RESOLUTION_OUTPUT_CONTRACT,
    SyntheticInputBundle,
    SyntheticMaster,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticResolutionArtifact,
    SyntheticResolutionArtifacts,
    SyntheticRun,
    generate_synthetic_pcf_run,
    write_synthetic_run,
)

__all__ = [
    "ExpectedClaim",
    "ExpectedArtifactRef",
    "ExpectedDependencyRef",
    "ExpectedDerivedClaim",
    "ExpectedFailedClaim",
    "ExpectedHazard",
    "ExpectedObligation",
    "ExpectedReceipt",
    "ExpectedResolutionArtifact",
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "RawElectricityRow",
    "RESOLUTION_OUTPUT_CONTRACT",
    "SyntheticInputBundle",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticPcfAdapter",
    "SyntheticRawSources",
    "SyntheticResolutionArtifact",
    "SyntheticResolutionArtifacts",
    "SyntheticRun",
    "SyntheticScenarioConfig",
    "generate_synthetic_pcf_run",
    "write_synthetic_run",
]
