import json

import pytest

from comp.persistence.codec import encode_persistence_json
from comp.persistence.mysql import commit_receipt_to_body
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


def test_comp_scenario_cli_validates_and_runs_prepared_bundle(tmp_path, capsys):
    from comp.cli.scenario import main

    report_path = tmp_path / "reports" / "cli.json"
    manifest_path = _write_prepared_scenario(tmp_path)

    assert main(["scenario", "validate", str(manifest_path)]) == 0
    assert "fixture_public_projection" in capsys.readouterr().out

    assert main(["scenario", "run", str(manifest_path), "--report", str(report_path)]) == 0
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

    runtime_case_path.write_text(
        json.dumps(
            {
                "case_id": "fixture-case",
                "receipts": [commit_receipt_to_body(case.receipt)],
                "projections": [
                    {
                        "public_row_id": "public-row-1",
                        "projection_id": "public-row",
                        "draft_id": "draft-1",
                        "output_fields": ["site", "amount"],
                        "row": case.public_row,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    artifact_path.write_text(
        "\n".join(_artifact_payload(envelope) for envelope in store.envelopes()),
        encoding="utf-8",
    )

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


def _artifact_payload(envelope):
    return json.dumps(
        {
            "artifact_id": envelope.artifact_id,
            "artifact_kind": envelope.artifact_kind,
            "schema_version": envelope.schema_version,
            "body_digest": envelope.body_digest,
            "body": encode_persistence_json(envelope.body),
            "source_refs": encode_persistence_json(envelope.source_refs),
            "meta": encode_persistence_json(envelope.meta),
        },
        sort_keys=True,
    )
