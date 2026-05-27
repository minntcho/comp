"""Comp-backed product facade observation lab."""

from examples.product_facade_lab.bundle import (
    verify_verification_bundle,
    verify_verification_bundle_file,
    verification_input_from_bundle,
    verification_input_to_bundle,
)
from examples.product_facade_lab.runtime import (
    ArtifactTouchLog,
    ArtifactTouchLogComparison,
    CompCompatibleVerificationInput,
    CompVerificationOutput,
    ProductAudit,
    ProductFacadeRuntime,
    ProductInput,
    ProductPolicyPreflightInput,
    ProductPublicRow,
    ProductRequiredAction,
    ProductRun,
    ProductWitness,
    compare_touch_logs,
    verify_comp_compatible_input,
)

__all__ = [
    "ArtifactTouchLog",
    "ArtifactTouchLogComparison",
    "CompCompatibleVerificationInput",
    "CompVerificationOutput",
    "ProductAudit",
    "ProductFacadeRuntime",
    "ProductInput",
    "ProductPolicyPreflightInput",
    "ProductPublicRow",
    "ProductRequiredAction",
    "ProductRun",
    "ProductWitness",
    "compare_touch_logs",
    "verify_comp_compatible_input",
    "verify_verification_bundle",
    "verify_verification_bundle_file",
    "verification_input_from_bundle",
    "verification_input_to_bundle",
]
