from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest

from comp.compiler_tool import resolve_reference_grounded_calculation
from comp.scenarios.synthetic import (
    SyntheticInputLoadError,
    SyntheticPcfAdapter,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
    load_synthetic_input_bundle,
    write_synthetic_run,
)
from tests.support.synthetic.oracle_assertions import (
    assert_synthetic_oracle_matches_report,
)


def test_synthetic_run_writer_lives_outside_generator_module() -> None:
    from comp.scenarios.synthetic.writer import write_synthetic_run as writer

    assert write_synthetic_run is writer
    assert writer.__module__ == "comp.scenarios.synthetic.writer"


def test_synthetic_data_models_live_outside_generator_module() -> None:
    from comp.scenarios.synthetic.models import SyntheticRun as model_run
    from comp.scenarios.synthetic.sources import (
        build_synthetic_loaded_source as source_builder,
    )

    assert generate_synthetic_pcf_run(
        SyntheticScenarioConfig.pcf_smoke(seed=7)
    ).__class__ is model_run
    assert model_run.__module__ == "comp.scenarios.synthetic.models"
    assert load_synthetic_input_bundle.__globals__["build_synthetic_loaded_source"] is (
        source_builder
    )


def test_synthetic_expected_receipt_oracle_lives_outside_generator_module() -> None:
    from comp.scenarios.synthetic.oracle import (
        calculation_obligation_id,
        expected_smoke_receipt,
        reference_search_obligation_id,
    )
    from comp.scenarios.synthetic.run_builders import build_synthetic_pcf_smoke_run

    config = SyntheticScenarioConfig.pcf_smoke(seed=7)
    run = generate_synthetic_pcf_run(config)
    derived_value = run.oracle.expected_derived_claims[0].value

    assert expected_smoke_receipt.__module__ == "comp.scenarios.synthetic.oracle"
    assert build_synthetic_pcf_smoke_run.__globals__["expected_smoke_receipt"] is (
        expected_smoke_receipt
    )
    assert run.oracle.expected_receipt == expected_smoke_receipt(
        config,
        source_witness_id=f"witness:{config.source_row_id}:electricity_kwh",
        derived_value=derived_value,
    )
    assert run.oracle.expected_receipt is not None
    assert run.oracle.expected_receipt.resolved_obligation_ids == (
        reference_search_obligation_id(config),
        calculation_obligation_id(config),
    )


def test_synthetic_anomaly_specs_live_outside_generator_module() -> None:
    from comp.scenarios.synthetic.anomaly_specs import (
        anomaly_specs,
        missing_unit_resolution_artifact,
    )
    from comp.scenarios.synthetic.run_builders import (
        build_synthetic_pcf_anomaly_run,
        build_synthetic_pcf_resolution_run,
    )

    config = SyntheticScenarioConfig.pcf_anomaly(seed=11)
    run = generate_synthetic_pcf_run(config)
    specs = anomaly_specs(config)

    assert anomaly_specs.__module__ == "comp.scenarios.synthetic.anomaly_specs"
    assert build_synthetic_pcf_anomaly_run.__globals__["anomaly_specs"] is anomaly_specs
    assert tuple(spec["row"] for spec in specs) == run.raw_sources.electricity_rows
    assert tuple(spec["anomaly"] for spec in specs) == run.oracle.injected_anomalies

    resolution_run = generate_synthetic_pcf_run(
        SyntheticScenarioConfig.pcf_resolution(seed=17)
    )
    assert resolution_run.resolution_artifacts.unit_witnesses == (
        missing_unit_resolution_artifact(resolution_run.raw_sources.electricity_rows[0]),
    )
    assert build_synthetic_pcf_resolution_run.__globals__[
        "missing_unit_resolution_artifact"
    ] is missing_unit_resolution_artifact


def test_synthetic_run_builders_live_outside_generator_module() -> None:
    from comp.scenarios.synthetic.run_builders import (
        build_synthetic_pcf_anomaly_run,
        build_synthetic_pcf_resolution_run,
        build_synthetic_pcf_smoke_run,
    )

    smoke_config = SyntheticScenarioConfig.pcf_smoke(seed=7)
    resolution_config = SyntheticScenarioConfig.pcf_resolution(seed=17)
    anomaly_config = SyntheticScenarioConfig.pcf_anomaly(seed=11)

    assert (
        build_synthetic_pcf_smoke_run.__module__
        == "comp.scenarios.synthetic.run_builders"
    )
    assert generate_synthetic_pcf_run.__globals__["build_synthetic_pcf_smoke_run"] is (
        build_synthetic_pcf_smoke_run
    )
    assert generate_synthetic_pcf_run(smoke_config) == build_synthetic_pcf_smoke_run(
        smoke_config
    )
    assert generate_synthetic_pcf_run(
        resolution_config
    ) == build_synthetic_pcf_resolution_run(resolution_config)
    assert generate_synthetic_pcf_run(anomaly_config) == build_synthetic_pcf_anomaly_run(
        anomaly_config
    )


def test_synthetic_pcf_fixtures_live_outside_run_builders_module() -> None:
    from comp.scenarios.synthetic.pcf_fixtures import (
        calculate_co2e_value,
        electricity_expected_claim,
        electricity_source_map,
        pcf_master,
        pcf_reference_record,
    )
    from comp.scenarios.synthetic.run_builders import build_synthetic_pcf_smoke_run

    config = SyntheticScenarioConfig.pcf_smoke(seed=7)
    run = build_synthetic_pcf_smoke_run(config)
    raw_row = run.raw_sources.electricity_rows[0]

    assert pcf_master.__module__ == "comp.scenarios.synthetic.pcf_fixtures"
    assert build_synthetic_pcf_smoke_run.__globals__["pcf_master"] is pcf_master
    assert build_synthetic_pcf_smoke_run.__globals__["calculate_co2e_value"] is (
        calculate_co2e_value
    )
    assert run.master == pcf_master(config)
    assert run.master.reference_catalog == (pcf_reference_record(config),)
    assert run.oracle.expected_derived_claims[0].value == calculate_co2e_value(
        raw_row.amount,
        config.factor_value,
    )
    assert run.oracle.expected_claims == (
        electricity_expected_claim(config.input_claim_id, raw_row),
    )
    assert run.oracle.source_to_expected_claim_map == (
        electricity_source_map(config.input_claim_id, raw_row),
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
    assert run.manifest["sources"] == [
        {
            "source_ref": "reference_catalog.csv",
            "role": "master_reference_catalog",
            "path": "master/reference_catalog.csv",
            "media_type": "text/csv",
            "schema_id": "synthetic.master_reference_catalog.v1",
        },
        {
            "source_ref": "sites.csv",
            "role": "master_sites",
            "path": "master/sites.csv",
            "media_type": "text/csv",
            "schema_id": "synthetic.master_sites.v1",
        },
        {
            "source_ref": "products.csv",
            "role": "master_products",
            "path": "master/products.csv",
            "media_type": "text/csv",
            "schema_id": "synthetic.master_products.v1",
        },
        {
            "source_ref": "erp_electricity.csv",
            "role": "raw_source",
            "path": "raw_sources/erp_electricity.csv",
            "media_type": "text/csv",
            "schema_id": "synthetic.erp_electricity.v1",
        },
    ]

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


def test_synthetic_pcf_resolution_generator_writes_recovery_contract(
    tmp_path: Path,
) -> None:
    config = SyntheticScenarioConfig.pcf_resolution(seed=17)

    run = generate_synthetic_pcf_run(config)
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-resolution")

    assert run.manifest["scenario_id"] == "synthetic_pcf.resolution.v1"
    assert run.output_contract == (
        "master",
        "raw_sources",
        "resolution_artifacts",
        "oracle",
    )
    assert run.manifest["sources"][-1] == {
        "source_ref": "unit_witnesses.csv",
        "role": "resolution_unit_witness",
        "path": "resolution_artifacts/unit_witnesses.csv",
        "media_type": "text/csv",
        "schema_id": "synthetic.resolution_unit_witnesses.v1",
    }
    assert (run_dir / "resolution_artifacts" / "unit_witnesses.csv").is_file()
    assert (run_dir / "oracle" / "expected_resolution_artifacts.csv").is_file()
    assert (run_dir / "oracle" / "expected_resolved_obligations.csv").is_file()
    assert (run_dir / "oracle" / "expected_receipt.json").is_file()
    assert not (run_dir / "truth").exists()

    raw_rows = _read_csv(run_dir / "raw_sources" / "erp_electricity.csv")
    resolution_artifacts = _read_csv(
        run_dir / "resolution_artifacts" / "unit_witnesses.csv"
    )
    expected_resolved = _read_csv(
        run_dir / "oracle" / "expected_resolved_obligations.csv"
    )

    assert raw_rows[0]["source_row_id"] == "ERP-SYN-PCF-MISSING-UNIT"
    assert raw_rows[0]["unit"] == ""
    assert resolution_artifacts == [
        {
            "artifact_id": "synthetic-resolution:missing_unit:kwh",
            "obligation_id": "synthetic-obligation:missing_unit",
            "source_row_id": "ERP-SYN-PCF-MISSING-UNIT",
            "field": "unit",
            "resolved_value": "kWh",
            "witness_id": "resolution-witness:ERP-SYN-PCF-MISSING-UNIT:unit",
            "source_ref": "unit_witnesses.csv",
            "rationale": "operator supplied the omitted electricity unit",
        }
    ]
    assert expected_resolved == [
        {
            "obligation_id": "synthetic-obligation:missing_unit",
            "kind": "find_source_witness",
            "field": "unit",
            "reason": "missing_unit",
        },
        {
            "obligation_id": (
                "resolve:pcf.electricity_factor_multiplication.v1:"
                "synthetic-pcf-resolution:electricity:co2e_kg:"
                "reference_search_required"
            ),
            "kind": "reference_search_required",
            "field": "co2e_kg",
            "reason": "unknown_reference",
        },
        {
            "obligation_id": (
                "calculation:pcf.electricity_factor_multiplication.v1:"
                "synthetic-pcf-resolution:electricity:co2e_kg:unknown_reference"
            ),
            "kind": "calculation_blocked",
            "field": "co2e_kg",
            "reason": "unknown_reference",
        },
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


def test_synthetic_input_loader_roundtrips_disk_sources_without_oracle(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")
    shutil.rmtree(run_dir / "oracle")

    input_bundle = load_synthetic_input_bundle(run_dir)
    adapter = SyntheticPcfAdapter(input_bundle)
    report = resolve_reference_grounded_calculation(
        adapter.blocked_report(),
        adapter.reference_catalog(),
        query_for_obligation=adapter.query_for_obligation,
        criteria=adapter.reference_selection_criteria(),
        input_claim=adapter.input_claim(),
        formula=adapter.formula(),
        output_claim_id=adapter.output_claim_id,
    )

    assert input_bundle.raw_sources == run.input_bundle.raw_sources
    assert input_bundle.master == run.input_bundle.master
    assert [
        (source.role, source.source_ref, source.row_count)
        for source in input_bundle.loaded_sources
    ] == [
        ("master_reference_catalog", "reference_catalog.csv", 1),
        ("master_sites", "sites.csv", 1),
        ("master_products", "products.csv", 1),
        ("raw_source", "erp_electricity.csv", 1),
    ]
    assert all(
        source.content_digest.startswith("sha256:")
        for source in input_bundle.loaded_sources
    )
    assert report.status == "accepted"
    assert {witness.source for witness in report.evidence_witnesses} == {
        "raw_sources/erp_electricity.csv",
    }


def test_synthetic_input_loader_roundtrips_resolution_artifacts_without_oracle(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_resolution(seed=17))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-resolution")
    shutil.rmtree(run_dir / "oracle")

    input_bundle = load_synthetic_input_bundle(run_dir)

    assert input_bundle.resolution_artifacts == run.input_bundle.resolution_artifacts
    assert [
        (source.role, source.source_ref, source.row_count)
        for source in input_bundle.loaded_sources
    ] == [
        ("master_reference_catalog", "reference_catalog.csv", 1),
        ("master_sites", "sites.csv", 1),
        ("master_products", "products.csv", 1),
        ("raw_source", "erp_electricity.csv", 1),
        ("resolution_unit_witness", "unit_witnesses.csv", 1),
    ]


def test_synthetic_input_loader_fingerprints_loaded_source_content(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")
    first = load_synthetic_input_bundle(run_dir)

    raw_path = run_dir / "raw_sources" / "erp_electricity.csv"
    rows = _read_csv(raw_path)
    rows[0]["amount"] = "1300"
    _write_csv(raw_path, list(rows[0]), rows)

    second = load_synthetic_input_bundle(run_dir)

    first_raw = next(
        source for source in first.loaded_sources if source.role == "raw_source"
    )
    second_raw = next(
        source for source in second.loaded_sources if source.role == "raw_source"
    )
    assert first_raw.content_digest != second_raw.content_digest


def test_synthetic_generated_and_disk_loaded_sources_share_fingerprints(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")

    input_bundle = load_synthetic_input_bundle(run_dir)

    assert input_bundle.loaded_sources == run.input_bundle.loaded_sources


def test_synthetic_adapter_cites_loaded_sources_as_dependencies(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")
    adapter = SyntheticPcfAdapter(load_synthetic_input_bundle(run_dir))

    fingerprints = adapter.dependency_fingerprints()
    bodies = adapter.dependency_artifact_bodies()

    assert [
        (fingerprint.dependency_kind, fingerprint.dependency_id)
        for fingerprint in fingerprints
    ] == [
        (
            "synthetic_manifest",
            "synthetic_manifest:synthetic_pcf.smoke.v1:seed-7",
        ),
        (
            "synthetic_source_input",
            (
                "synthetic_source_input:synthetic_pcf.smoke.v1:"
                "seed-7:master_reference_catalog:reference_catalog.csv"
            ),
        ),
        (
            "synthetic_source_input",
            (
                "synthetic_source_input:synthetic_pcf.smoke.v1:"
                "seed-7:master_sites:sites.csv"
            ),
        ),
        (
            "synthetic_source_input",
            (
                "synthetic_source_input:synthetic_pcf.smoke.v1:"
                "seed-7:master_products:products.csv"
            ),
        ),
        (
            "synthetic_source_input",
            (
                "synthetic_source_input:synthetic_pcf.smoke.v1:"
                "seed-7:raw_source:erp_electricity.csv"
            ),
        ),
    ]
    for fingerprint in fingerprints:
        body = bodies[(fingerprint.dependency_kind, fingerprint.dependency_id)]
        assert body["fingerprint"] == fingerprint.fingerprint
        assert body["digest_alg"] == fingerprint.digest_alg


def test_synthetic_input_loader_uses_manifest_media_type_not_file_extension(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")
    alternate_path = run_dir / "raw_sources" / "erp_electricity.raw"
    (run_dir / "raw_sources" / "erp_electricity.csv").replace(alternate_path)
    manifest = _read_json(run_dir / "manifest.json")
    manifest["sources"][-1]["path"] = "raw_sources/erp_electricity.raw"
    _write_json(run_dir / "manifest.json", manifest)

    input_bundle = load_synthetic_input_bundle(run_dir)

    assert input_bundle.raw_sources == run.input_bundle.raw_sources


def test_synthetic_input_loader_rejects_unsupported_manifest_source(
    tmp_path: Path,
) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-smoke")
    manifest = _read_json(run_dir / "manifest.json")
    manifest["sources"][-1]["media_type"] = "application/parquet"
    _write_json(run_dir / "manifest.json", manifest)

    with pytest.raises(
        SyntheticInputLoadError,
        match="unsupported synthetic source loader",
    ):
        load_synthetic_input_bundle(run_dir)


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


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    headers: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
