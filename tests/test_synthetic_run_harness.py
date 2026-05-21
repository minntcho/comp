from __future__ import annotations

import json

from comp.persistence import ArtifactRef
from comp.scenarios.synthetic import SyntheticScenarioConfig
from tests.support.synthetic import materialize_synthetic_run


def test_synthetic_run_harness_materializes_smoke_receipt_flow(tmp_path) -> None:
    harness = materialize_synthetic_run(
        SyntheticScenarioConfig.pcf_smoke(seed=7),
        tmp_path,
    )

    assert harness.run_dir.name == "synthetic_pcf.smoke.v1-seed-7"
    assert (harness.run_dir / "raw_sources" / "erp_electricity.csv").is_file()
    assert (harness.run_dir / "oracle" / "expected_derived_claims.csv").is_file()
    assert (harness.run_dir / "oracle" / "expected_receipt.json").is_file()
    assert harness.oracle_checked is True
    assert harness.receipt_oracle_checked is True
    assert harness.report.status == "accepted"
    assert harness.preparation.decision.status == "commit"
    assert harness.preparation.receipt is not None
    assert harness.projection == {
        "electricity_kwh": 1200,
        "co2e_kg": 504.0,
    }
    assert harness.replay_report is not None
    assert harness.replay_report.public_row == harness.projection
    assert (
        ArtifactRef("commit-package:product:synthetic-pcf-smoke-1", "commit_package")
        in harness.replay_report.artifact_refs
    )
    assert (
        ArtifactRef(
            "governance-decision:commit-package:product:synthetic-pcf-smoke-1",
            "governance_decision",
        )
        in harness.replay_report.artifact_refs
    )
    assert (
        ArtifactRef(
            "synthetic_manifest:synthetic_pcf.smoke.v1:seed-7",
            "synthetic_manifest",
        )
        in harness.replay_report.artifact_refs
    )
    expected_receipt = json.loads(
        (harness.run_dir / "oracle" / "expected_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert expected_receipt["public_row_id"] == "public-row:synthetic-pcf-smoke-1"
    assert expected_receipt["projection_id"] == "synthetic-pcf-public-row"
    assert expected_receipt["authorized_fields"] == ["electricity_kwh", "co2e_kg"]


def test_synthetic_run_harness_materializes_anomaly_hold_flow(tmp_path) -> None:
    harness = materialize_synthetic_run(
        SyntheticScenarioConfig.pcf_anomaly(seed=11),
        tmp_path,
    )

    assert harness.run_dir.name == "synthetic_pcf.anomaly.v1-seed-11"
    assert (harness.run_dir / "oracle" / "injected_anomalies.csv").is_file()
    assert (harness.run_dir / "oracle" / "expected_failed_claims.csv").is_file()
    assert not (harness.run_dir / "oracle" / "expected_receipt.json").exists()
    assert harness.oracle_checked is True
    assert harness.receipt_oracle_checked is False
    assert harness.report.status == "blocked"
    assert harness.preparation.decision.status == "hold"
    assert harness.preparation.receipt is None
    assert harness.projection is None
    assert harness.replay_report is None


def test_synthetic_run_harness_materializes_resolution_commit_flow(tmp_path) -> None:
    harness = materialize_synthetic_run(
        SyntheticScenarioConfig.pcf_resolution(seed=17),
        tmp_path,
    )

    assert harness.run_dir.name == "synthetic_pcf.resolution.v1-seed-17"
    assert (
        harness.run_dir / "resolution_artifacts" / "unit_witnesses.csv"
    ).is_file()
    assert (
        harness.run_dir / "oracle" / "expected_resolved_obligations.csv"
    ).is_file()
    assert harness.oracle_checked is True
    assert harness.receipt_oracle_checked is True
    assert harness.report.status == "accepted"
    assert harness.report.obligations == ()
    assert harness.report.hazards == ()
    assert tuple(
        obligation.obligation_id for obligation in harness.report.resolved_obligations
    ) == (
        "synthetic-obligation:missing_unit",
        "resolve:pcf.electricity_factor_multiplication.v1:"
        "synthetic-pcf-resolution:electricity:co2e_kg:reference_search_required",
        "calculation:pcf.electricity_factor_multiplication.v1:"
        "synthetic-pcf-resolution:electricity:co2e_kg:unknown_reference",
    )
    assert harness.preparation.decision.status == "commit"
    assert harness.preparation.receipt is not None
    assert harness.projection == {
        "electricity_kwh": 1200,
        "co2e_kg": 504.0,
    }
    assert harness.replay_report is not None
    assert harness.replay_report.public_row == harness.projection
