from __future__ import annotations

from pathlib import Path

from comp.runtime import TrustRuntime
from comp.scenario_contracts.artifacts import load_artifact_envelopes
from comp.scenario_contracts.case import load_runtime_case
from comp.scenario_contracts.manifest import ScenarioManifest, load_manifest
from comp.scenario_contracts.report import write_report
from comp.scenario_contracts.result import ScenarioResult


def run_scenario(
    manifest: str | Path | ScenarioManifest,
    *,
    runtime: TrustRuntime | None = None,
    report_path: str | Path | None = None,
) -> ScenarioResult:
    scenario_manifest = (
        load_manifest(manifest)
        if not isinstance(manifest, ScenarioManifest)
        else manifest
    )
    runtime_case = load_runtime_case(scenario_manifest.runtime_case_path)
    artifact_envelopes = load_artifact_envelopes(
        scenario_manifest.artifact_envelopes_path
    )
    trust_runtime = runtime if runtime is not None else TrustRuntime()
    result = trust_runtime.run(
        scenario_id=scenario_manifest.scenario_id,
        runtime_case=runtime_case,
        artifact_envelopes=artifact_envelopes,
        invariants=scenario_manifest.invariants,
    )
    selected_report_path = (
        Path(report_path) if report_path is not None else scenario_manifest.report_path
    )
    if selected_report_path is None:
        return result
    report_path = write_report(result, selected_report_path)
    return ScenarioResult(
        scenario_id=result.scenario_id,
        status=result.status,
        artifact_count=result.artifact_count,
        receipt_count=result.receipt_count,
        public_row_count=result.public_row_count,
        replay_checked_count=result.replay_checked_count,
        replay_failed_count=result.replay_failed_count,
        invariant_results=result.invariant_results,
        performance=result.performance,
        report_path=str(report_path),
    )


__all__ = ["run_scenario"]
