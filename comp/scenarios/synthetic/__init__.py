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
    ExpectedSourceMap,
    InjectedAnomaly,
    MasterReferenceRecord,
    RawElectricityRow,
    SyntheticInputBundle,
    SyntheticMaster,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticRun,
    generate_synthetic_pcf_run,
    write_synthetic_run,
)
from comp.scenarios.synthetic.loaders import (
    SyntheticInputLoadError,
    SyntheticSourceDescriptor,
    load_synthetic_input_bundle,
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
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "RawElectricityRow",
    "SyntheticInputBundle",
    "SyntheticInputLoadError",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticPcfAdapter",
    "SyntheticRawSources",
    "SyntheticRun",
    "SyntheticScenarioConfig",
    "SyntheticSourceDescriptor",
    "generate_synthetic_pcf_run",
    "load_synthetic_input_bundle",
    "write_synthetic_run",
]
