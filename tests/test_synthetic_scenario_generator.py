from __future__ import annotations

import csv
from pathlib import Path

from comp.scenarios.synthetic import (
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
    write_synthetic_run,
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
