"""Synthetic scenario generator for comp tests.

This package produces raw inputs and oracle expectations. It does not validate
claims, issue receipts, or authorize public output.
"""

from comp.scenarios.synthetic.adapters import SyntheticPcfAdapter
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.generator import generate_synthetic_pcf_run
from comp.scenarios.synthetic.models import (
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
    SyntheticLoadedSource,
    SyntheticMaster,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticResolutionArtifact,
    SyntheticResolutionArtifacts,
    SyntheticRun,
)
from comp.scenarios.synthetic.sources import (
    build_synthetic_loaded_source,
    build_synthetic_loaded_sources,
    synthetic_source_input_dependency_id,
)
from comp.scenarios.synthetic.loaders import (
    SyntheticInputLoadError,
    SyntheticSourceDescriptor,
    load_synthetic_input_bundle,
)
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
)
from comp.scenarios.synthetic.writer import write_synthetic_run

__all__ = [
    "AllocationSupport",
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
    "PromotionClaimIds",
    "RawElectricityRow",
    "ReportingPeriodSupport",
    "RESOLUTION_OUTPUT_CONTRACT",
    "SiteAliasSupport",
    "SyntheticInputBundle",
    "SyntheticInputLoadError",
    "SyntheticLoadedSource",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticPcfAdapter",
    "SyntheticRawSources",
    "SyntheticResolutionArtifact",
    "SyntheticResolutionArtifacts",
    "SyntheticRun",
    "SyntheticScenarioConfig",
    "SyntheticRawClaimPromotionProfile",
    "SyntheticSourceDescriptor",
    "UnitConversionSupport",
    "build_synthetic_loaded_source",
    "build_synthetic_loaded_sources",
    "generate_synthetic_pcf_run",
    "load_synthetic_input_bundle",
    "promote_raw_claim_hypothesis",
    "synthetic_source_input_dependency_id",
    "write_synthetic_run",
]
