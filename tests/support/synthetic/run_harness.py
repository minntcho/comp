from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from comp import PublicOutputSpec, build_public_output
from comp.compiler_tool import (
    CommitPreparation,
    ValidationReport,
    prepare_commit,
    resolve_reference_grounded_calculation,
)
from comp.persistence import ProjectionReplayReport
from comp.scenarios.synthetic import (
    SyntheticOracle,
    SyntheticPcfAdapter,
    SyntheticRun,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
    load_synthetic_input_bundle,
    write_synthetic_run,
)
from tests.support.synthetic.oracle_assertions import (
    assert_synthetic_oracle_matches_report,
    assert_synthetic_receipt_oracle_matches,
    load_synthetic_oracle,
)
from tests.support.synthetic.replay import (
    replay_synthetic_projection,
    synthetic_replay_bundle,
)


@dataclass(frozen=True)
class MaterializedSyntheticRun:
    run: SyntheticRun
    run_dir: Path
    oracle: SyntheticOracle
    adapter: SyntheticPcfAdapter
    report: ValidationReport
    preparation: CommitPreparation
    projection: dict[str, Any] | None
    replay_report: ProjectionReplayReport | None
    oracle_checked: bool
    receipt_oracle_checked: bool


def materialize_synthetic_run(
    config: SyntheticScenarioConfig,
    base_dir: Path,
) -> MaterializedSyntheticRun:
    run = generate_synthetic_pcf_run(config)
    run_dir = write_synthetic_run(
        run,
        base_dir / f"{config.scenario_id}-seed-{config.seed}",
    )
    oracle = load_synthetic_oracle(run_dir / "oracle")
    adapter = SyntheticPcfAdapter(load_synthetic_input_bundle(run_dir))
    report = _compile_report(adapter)
    preparation = prepare_commit(
        report,
        subject_id=adapter.subject_id,
        public_row_id=adapter.public_row_id,
        projection_id=adapter.projection_id,
        profile_id=adapter.profile_id,
        dependency_fingerprints=adapter.dependency_fingerprints(),
    )
    projection_spec = PublicOutputSpec(adapter.projection_id, adapter.projection_fields)
    projection = _project_if_authorized(adapter, report, preparation, projection_spec)
    replay_report = _replay_if_authorized(
        adapter,
        report,
        preparation,
        projection,
        projection_spec,
    )

    assert_synthetic_oracle_matches_report(oracle, report)
    assert_synthetic_receipt_oracle_matches(
        oracle,
        preparation.receipt,
        replay_report,
    )

    return MaterializedSyntheticRun(
        run=run,
        run_dir=run_dir,
        oracle=oracle,
        adapter=adapter,
        report=report,
        preparation=preparation,
        projection=projection,
        replay_report=replay_report,
        oracle_checked=True,
        receipt_oracle_checked=oracle.expected_receipt is not None,
    )


def _compile_report(adapter: SyntheticPcfAdapter) -> ValidationReport:
    if adapter.has_resolution_artifacts():
        return resolve_reference_grounded_calculation(
            adapter.resolution_seed_report(),
            adapter.reference_catalog(),
            query_for_obligation=adapter.query_for_obligation,
            criteria=adapter.reference_selection_criteria(),
            input_claim=adapter.resolved_input_claim(),
            formula=adapter.formula(),
            output_claim_id=adapter.output_claim_id,
        )
    if adapter.config.anomalies:
        return adapter.anomaly_report()
    return resolve_reference_grounded_calculation(
        adapter.blocked_report(),
        adapter.reference_catalog(),
        query_for_obligation=adapter.query_for_obligation,
        criteria=adapter.reference_selection_criteria(),
        input_claim=adapter.input_claim(),
        formula=adapter.formula(),
        output_claim_id=adapter.output_claim_id,
    )


def _project_if_authorized(
    adapter: SyntheticPcfAdapter,
    report: ValidationReport,
    preparation: CommitPreparation,
    projection_spec: PublicOutputSpec,
) -> dict[str, Any] | None:
    if preparation.receipt is None:
        return None
    return build_public_output(
        adapter.projection_source(report),
        projection_spec,
        receipt=preparation.receipt,
    )


def _replay_if_authorized(
    adapter: SyntheticPcfAdapter,
    report: ValidationReport,
    preparation: CommitPreparation,
    projection: dict[str, Any] | None,
    projection_spec: PublicOutputSpec,
) -> ProjectionReplayReport | None:
    if preparation.receipt is None or projection is None:
        return None
    bundle = synthetic_replay_bundle(
        report,
        preparation,
        adapter.dependency_artifact_bodies(),
    )
    return replay_synthetic_projection(
        projection,
        projection_spec,
        preparation,
        bundle=bundle,
    )


__all__ = ["MaterializedSyntheticRun", "materialize_synthetic_run"]
