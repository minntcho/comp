"""Public scenario bridge contracts for external conformance packs."""

from comp.scenario_contracts.case import (
    RuntimeCase,
    RuntimeProjection,
    load_runtime_case,
    runtime_case_from_mapping,
    runtime_case_to_mapping,
    runtime_projection_to_mapping,
    write_runtime_case,
)
from comp.scenario_contracts.artifacts import (
    artifact_envelope_from_mapping,
    artifact_envelope_to_mapping,
    load_artifact_envelopes,
    write_artifact_envelopes,
)
from comp.scenario_contracts.examples import (
    ScenarioBundleExistsError,
    write_public_projection_smoke_bundle,
)
from comp.scenario_contracts.manifest import (
    ScenarioManifest,
    ScenarioManifestError,
    load_manifest,
)
from comp.scenario_contracts.report import write_report
from comp.scenario_contracts.result import InvariantResult, ScenarioResult


def __getattr__(name: str):
    if name == "run_scenario":
        from comp.scenario_contracts.runner import run_scenario

        return run_scenario
    raise AttributeError(name)

__all__ = [
    "InvariantResult",
    "RuntimeCase",
    "RuntimeProjection",
    "ScenarioBundleExistsError",
    "ScenarioManifest",
    "ScenarioManifestError",
    "ScenarioResult",
    "artifact_envelope_from_mapping",
    "artifact_envelope_to_mapping",
    "load_artifact_envelopes",
    "load_manifest",
    "load_runtime_case",
    "run_scenario",
    "runtime_case_from_mapping",
    "runtime_case_to_mapping",
    "runtime_projection_to_mapping",
    "write_artifact_envelopes",
    "write_public_projection_smoke_bundle",
    "write_report",
    "write_runtime_case",
]
