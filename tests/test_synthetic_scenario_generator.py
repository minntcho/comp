from __future__ import annotations

import csv
from pathlib import Path

import pytest

from comp.scenarios.synthetic import (
    SyntheticPcfAdapter,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
    write_synthetic_run,
)
from tests.support.synthetic.oracle_assertions import (
    assert_synthetic_oracle_matches_report,
)


def test_synthetic_pcf_generator_writes_oracle_not_truth(tmp_path: Path) -> None:
    config = SyntheticScenarioConfig.pcf_smoke(seed=7)

    run = generate_synthetic_pcf_run(config)
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")

    assert run.manifest["generator"] == "comp.scenarios.synthetic"
    assert run.manifest["scenario_id"] == "synthetic_pcf.smoke.v1"
    assert run.manifest["reproducibility"]["seed"] == 7
    assert run.manifest["reproducibility"]["config_hash"].startswith("sha256:")
    assert run.output_contract == ("master", "raw_sources", "oracle")

    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "master" / "reference_catalog.csv").is_file()
    assert (run_dir / "raw_sources" / "erp_electricity.csv").is_file()
    assert (run_dir / "oracle" / "expected_claims.csv").is_file()
    assert (run_dir / "oracle" / "expected_derived_claims.csv").is_file()
    assert (run_dir / "oracle" / "source_to_expected_claim_map.csv").is_file()
    assert not (run_dir / "truth").exists()

    with (run_dir / "oracle" / "expected_derived_claims.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        derived = list(csv.DictReader(handle))

    assert derived == [
        {
            "claim_id": "synthetic-pcf-smoke:electricity:co2e_kg",
            "field": "co2e_kg",
            "value": "504.0",
            "unit": "kgCO2e",
            "formula_id": "pcf.electricity_factor_multiplication.v1",
        }
    ]


def test_synthetic_pcf_anomaly_generator_writes_pressure_oracle(
    tmp_path: Path,
) -> None:
    config = SyntheticScenarioConfig.pcf_anomaly(seed=11)

    run = generate_synthetic_pcf_run(config)
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-anomaly")

    assert run.manifest["scenario_id"] == "synthetic_pcf.anomaly.v1"
    assert run.manifest["reproducibility"]["seed"] == 11
    assert run.output_contract == ("master", "raw_sources", "oracle")
    assert tuple(item.anomaly_type for item in run.oracle.injected_anomalies) == (
        "missing_unit",
        "wrong_unit",
        "period_mismatch",
        "negative_amount",
        "site_alias",
    )

    assert (run_dir / "raw_sources" / "erp_electricity.csv").is_file()
    assert (run_dir / "oracle" / "injected_anomalies.csv").is_file()
    assert (run_dir / "oracle" / "expected_failed_claims.csv").is_file()
    assert (run_dir / "oracle" / "expected_obligations.csv").is_file()
    assert (run_dir / "oracle" / "expected_hazards.csv").is_file()
    assert not (run_dir / "truth").exists()

    raw_rows = _read_csv(run_dir / "raw_sources" / "erp_electricity.csv")
    injected = _read_csv(run_dir / "oracle" / "injected_anomalies.csv")
    failed = _read_csv(run_dir / "oracle" / "expected_failed_claims.csv")
    obligations = _read_csv(run_dir / "oracle" / "expected_obligations.csv")
    hazards = _read_csv(run_dir / "oracle" / "expected_hazards.csv")

    assert [row["source_row_id"] for row in raw_rows] == [
        "ERP-SYN-PCF-MISSING-UNIT",
        "ERP-SYN-PCF-WRONG-UNIT",
        "ERP-SYN-PCF-PERIOD-MISMATCH",
        "ERP-SYN-PCF-NEGATIVE-AMOUNT",
        "ERP-SYN-PCF-SITE-ALIAS",
    ]
    assert {row["source_ref"] for row in raw_rows} == {"erp_electricity.csv"}
    assert [row["anomaly_type"] for row in injected] == [
        "missing_unit",
        "wrong_unit",
        "period_mismatch",
        "negative_amount",
        "site_alias",
    ]
    assert [(row["field"], row["reason"]) for row in failed] == [
        ("unit", "unsupported_unit"),
        ("electricity_kwh", "negative_amount"),
    ]
    assert [row["obligation_id"] for row in obligations] == [
        "synthetic-obligation:missing_unit",
        "synthetic-obligation:wrong_unit",
        "synthetic-obligation:period_mismatch",
        "synthetic-obligation:negative_amount",
        "synthetic-obligation:site_alias",
    ]
    assert [(row["kind"], row["field"], row["severity"]) for row in hazards] == [
        ("missing_unit", "unit", "review"),
        ("period_mismatch", "period", "review"),
        ("invalid_activity_amount", "electricity_kwh", "block"),
        ("site_alias", "site_id", "review"),
    ]


def test_synthetic_pcf_anomaly_adapter_reports_raw_source_pressure() -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_anomaly(seed=11))
    adapter = SyntheticPcfAdapter(run.input_bundle)

    report = adapter.anomaly_report()

    assert_synthetic_oracle_matches_report(run.oracle, report)
    assert report.status == "blocked"
    assert {witness.source for witness in report.evidence_witnesses} == {
        "raw_sources/erp_electricity.csv",
    }


def test_synthetic_pcf_adapter_rejects_oracle_bearing_run() -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))

    with pytest.raises(TypeError, match="SyntheticInputBundle"):
        SyntheticPcfAdapter(run)  # type: ignore[arg-type]


def test_comp_core_does_not_import_synthetic_scenario_generator() -> None:
    root = Path(__file__).resolve().parents[1] / "comp"
    core_dirs = (
        root / "compiler_tool",
        root / "judgment",
        root / "persistence",
    )

    importing_files = [
        path
        for directory in core_dirs
        for path in directory.rglob("*.py")
        if "comp.scenarios" in path.read_text(encoding="utf-8")
    ]

    assert importing_files == []


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
