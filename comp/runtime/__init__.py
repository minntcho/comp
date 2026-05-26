"""Runtime primitives that execute the comp trust path without product ingestion."""

from comp.runtime.compiler_run_artifacts import (
    CompilerRunArtifactMaterializationError,
    ExternalArtifactMaterial,
    ExternalArtifactMaterialSource,
    materialize_compiler_run_artifacts,
)
from comp.runtime.trust_runtime import TrustRuntime
from comp.runtime.validation_handoff import ValidationHandoff, ValidationHandoffClaim

__all__ = [
    "CompilerRunArtifactMaterializationError",
    "ExternalArtifactMaterial",
    "ExternalArtifactMaterialSource",
    "TrustRuntime",
    "ValidationHandoff",
    "ValidationHandoffClaim",
    "materialize_compiler_run_artifacts",
]
