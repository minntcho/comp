from __future__ import annotations

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
    assert harness.oracle_checked is True
    assert harness.report.status == "accepted"
    assert harness.preparation.decision.status == "commit"
    assert harness.preparation.receipt is not None
    assert harness.projection == {
        "electricity_kwh": 1200,
        "co2e_kg": 504.0,
    }


def test_synthetic_run_harness_materializes_anomaly_hold_flow(tmp_path) -> None:
    harness = materialize_synthetic_run(
        SyntheticScenarioConfig.pcf_anomaly(seed=11),
        tmp_path,
    )

    assert harness.run_dir.name == "synthetic_pcf.anomaly.v1-seed-11"
    assert (harness.run_dir / "oracle" / "injected_anomalies.csv").is_file()
    assert (harness.run_dir / "oracle" / "expected_failed_claims.csv").is_file()
    assert harness.oracle_checked is True
    assert harness.report.status == "blocked"
    assert harness.preparation.decision.status == "hold"
    assert harness.preparation.receipt is None
    assert harness.projection is None
