import json
from pathlib import Path

import pytest

from comp.scenario_contracts import RuntimeCase, RuntimeProjection
from comp.scenario_contracts import write_artifact_envelopes, write_runtime_case
from tests.support.persistence_cases import artifact_store_for_receipt
from tests.support.persistence_cases import receipt_projection_case


def test_run_scenario_accepts_prepared_canonical_bundle(tmp_path):
    from comp.scenario_contracts import run_scenario

    manifest_path = _write_prepared_scenario(tmp_path)

    result = run_scenario(manifest_path)

    assert result.scenario_id == "fixture_public_projection"
    assert result.status == "passed"
    assert result.artifact_count == 9
    assert result.receipt_count == 1
    assert result.public_row_count == 1
    assert result.replay_checked_count == 1
    assert result.replay_failed_count == 0
    assert {item.name: item.status for item in result.invariant_results} == {
        "receipt_exists": "passed",
        "replay_succeeds": "passed",
        "all_public_rows_have_receipts": "passed",
        "projection_values_are_committed": "passed",
        "blocking_hazards_absent": "passed",
    }


def test_run_scenario_writes_json_report(tmp_path):
    from comp.scenario_contracts import run_scenario

    report_path = tmp_path / "reports" / "latest.json"
    manifest_path = _write_prepared_scenario(tmp_path, report_path=report_path)

    result = run_scenario(manifest_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.report_path == str(report_path)
    assert payload["scenario_id"] == "fixture_public_projection"
    assert payload["status"] == "passed"
    assert payload["counts"] == {
        "artifacts": 9,
        "receipts": 1,
        "public_rows": 1,
    }
    assert payload["replay"] == {
        "checked": 1,
        "failed": 0,
    }
    assert payload["invariants"][0] == {
        "name": "receipt_exists",
        "status": "passed",
        "message": "",
    }


def test_writer_helpers_round_trip_prepared_bundle(tmp_path):
    from comp.scenario_contracts import run_scenario

    case = receipt_projection_case(amount=125, site="plant-b")
    store = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    runtime_case_path = prepared / "runtime_case.json"
    artifact_path = prepared / "artifact_envelopes.jsonl"

    write_runtime_case(
        RuntimeCase(
            case_id="writer-round-trip",
            receipts=(case.receipt,),
            projections=(
                RuntimeProjection(
                    public_row_id="public-row-1",
                    projection_id="public-row",
                    draft_id="draft-1",
                    output_fields=("site", "amount"),
                    row=case.public_row,
                ),
            ),
        ),
        runtime_case_path,
    )
    write_artifact_envelopes(store.envelopes(), artifact_path)

    manifest_path = _write_manifest(
        tmp_path,
        report_path=tmp_path / "reports" / "latest.json",
    )
    result = run_scenario(manifest_path)

    runtime_payload = json.loads(runtime_case_path.read_text(encoding="utf-8"))
    first_artifact = json.loads(
        artifact_path.read_text(encoding="utf-8").splitlines()[0]
    )

    assert result.status == "passed"
    assert runtime_payload["case_id"] == "writer-round-trip"
    assert len(runtime_payload["receipts"]) == 1
    assert runtime_payload["projections"][0]["output_fields"] == ["site", "amount"]
    assert {
        "artifact_id",
        "artifact_kind",
        "schema_version",
        "body_digest",
        "body",
        "source_refs",
        "meta",
    } == set(first_artifact)


def test_public_contract_exports_bundle_loaders_and_writers():
    from comp.scenario_contracts import (
        artifact_envelope_from_mapping,
        artifact_envelope_to_mapping,
        load_artifact_envelopes,
        load_runtime_case,
        runtime_case_from_mapping,
        runtime_case_to_mapping,
        runtime_projection_to_mapping,
        ScenarioBundleExistsError,
        write_artifact_envelopes,
        write_public_projection_smoke_bundle,
        write_runtime_case,
    )

    assert ScenarioBundleExistsError is not None
    assert artifact_envelope_from_mapping is not None
    assert artifact_envelope_to_mapping is not None
    assert load_artifact_envelopes is not None
    assert load_runtime_case is not None
    assert runtime_case_from_mapping is not None
    assert runtime_case_to_mapping is not None
    assert runtime_projection_to_mapping is not None
    assert write_artifact_envelopes is not None
    assert write_public_projection_smoke_bundle is not None
    assert write_runtime_case is not None


def test_scenario_contract_examples_document_public_bundle_writer():
    examples = Path("docs/examples/scenario_contracts/README.md").read_text(
        encoding="utf-8"
    )

    assert "input_mode: canonical_bundle" in examples
    assert "write_runtime_case" in examples
    assert "write_artifact_envelopes" in examples
    assert "comp scenario init" in examples
    assert "comp scenario init --force" in examples
    assert "refuses to overwrite" in examples
    assert "comp scenario run" in examples
    assert "pre-trust" in examples


def test_run_scenario_rejects_pack_adapter_mode(tmp_path):
    from comp.scenario_contracts import ScenarioManifestError, run_scenario

    manifest_path = tmp_path / "scenario.json"
    manifest_path.write_text(
        json.dumps(
            {
                "id": "adapter_mode",
                "input_mode": "pack_adapter",
                "adapter": {"command": "python -m packs.example.prepare"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ScenarioManifestError, match="canonical_bundle"):
        run_scenario(manifest_path)


def test_run_scenario_rejects_unsupported_report_format(tmp_path):
    from comp.scenario_contracts import ScenarioManifestError, run_scenario

    manifest_path = _write_prepared_scenario(
        tmp_path,
        report_path=tmp_path / "reports" / "latest.html",
        report_format="html",
    )

    with pytest.raises(ScenarioManifestError, match="report.format"):
        run_scenario(manifest_path)


def test_comp_scenario_cli_initializes_runnable_smoke_bundle(tmp_path, capsys):
    from comp.cli.scenario import main

    target = tmp_path / "public_projection_smoke"
    report_path = target / "reports" / "latest.json"

    assert main(["scenario", "init", str(target)]) == 0
    init_output = capsys.readouterr().out

    assert "scenario.json" in init_output
    assert (target / "scenario.json").exists()
    assert (target / "prepared" / "runtime_case.json").exists()
    assert (target / "prepared" / "artifact_envelopes.jsonl").exists()

    assert (
        main(
            [
                "scenario",
                "run",
                str(target / "scenario.json"),
                "--report",
                str(report_path),
            ]
        )
        == 0
    )
    run_output = capsys.readouterr().out
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert "passed" in run_output
    assert report["scenario_id"] == "public_projection_smoke"
    assert report["status"] == "passed"


def test_comp_scenario_cli_init_refuses_to_overwrite_existing_bundle(
    tmp_path,
    capsys,
):
    from comp.cli.scenario import main

    target = tmp_path / "public_projection_smoke"
    assert main(["scenario", "init", str(target)]) == 0
    capsys.readouterr()
    marker = target / "prepared" / "runtime_case.json"
    marker.write_text("external pack data", encoding="utf-8")

    assert main(["scenario", "init", str(target)]) == 2
    output = capsys.readouterr()

    assert "already exists" in output.err
    assert marker.read_text(encoding="utf-8") == "external pack data"


def test_comp_scenario_cli_init_force_regenerates_existing_bundle(tmp_path, capsys):
    from comp.cli.scenario import main

    target = tmp_path / "public_projection_smoke"
    assert main(["scenario", "init", str(target)]) == 0
    capsys.readouterr()
    marker = target / "prepared" / "runtime_case.json"
    marker.write_text("external pack data", encoding="utf-8")

    assert main(["scenario", "init", "--force", str(target)]) == 0
    output = capsys.readouterr()
    payload = json.loads(marker.read_text(encoding="utf-8"))

    assert "created" in output.out
    assert payload["case_id"] == "public_projection_smoke"


def test_comp_scenario_cli_validates_and_runs_prepared_bundle(tmp_path, capsys):
    from comp.cli.scenario import main

    report_path = tmp_path / "reports" / "cli.json"
    manifest_path = _write_prepared_scenario(tmp_path)

    assert main(["scenario", "validate", str(manifest_path)]) == 0
    assert "fixture_public_projection" in capsys.readouterr().out

    assert (
        main(["scenario", "run", str(manifest_path), "--report", str(report_path)])
        == 0
    )
    output = capsys.readouterr().out

    assert "passed" in output
    assert report_path.exists()


def _write_prepared_scenario(tmp_path, *, report_path=None, report_format="json"):
    case = receipt_projection_case(amount=100, site="plant-a")
    store = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    prepared = tmp_path / "prepared"
    prepared.mkdir()
    runtime_case_path = prepared / "runtime_case.json"
    artifact_path = prepared / "artifact_envelopes.jsonl"
    manifest_path = tmp_path / "scenario.json"

    write_runtime_case(
        RuntimeCase(
            case_id="fixture-case",
            receipts=(case.receipt,),
            projections=(
                RuntimeProjection(
                    public_row_id="public-row-1",
                    projection_id="public-row",
                    draft_id="draft-1",
                    output_fields=("site", "amount"),
                    row=case.public_row,
                ),
            ),
        ),
        runtime_case_path,
    )
    write_artifact_envelopes(store.envelopes(), artifact_path)

    manifest = {
        "id": "fixture_public_projection",
        "input_mode": "canonical_bundle",
        "runtime_case": {"path": "prepared/runtime_case.json"},
        "artifact_envelopes": {"path": "prepared/artifact_envelopes.jsonl"},
        "expected": {
            "invariants": [
                "receipt_exists",
                "replay_succeeds",
                "all_public_rows_have_receipts",
                "projection_values_are_committed",
                "blocking_hazards_absent",
            ]
        },
    }
    if report_path is not None:
        manifest["report"] = {
            "format": report_format,
            "path": str(report_path),
        }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path


def _write_manifest(tmp_path, *, report_path=None):
    manifest_path = tmp_path / "scenario.json"
    manifest = {
        "id": "fixture_public_projection",
        "input_mode": "canonical_bundle",
        "runtime_case": {"path": "prepared/runtime_case.json"},
        "artifact_envelopes": {"path": "prepared/artifact_envelopes.jsonl"},
        "expected": {
            "invariants": [
                "receipt_exists",
                "replay_succeeds",
                "all_public_rows_have_receipts",
                "projection_values_are_committed",
                "blocking_hazards_absent",
            ]
        },
    }
    if report_path is not None:
        manifest["report"] = {
            "format": "json",
            "path": str(report_path),
        }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path
