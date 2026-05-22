import json
from pathlib import Path

from comp.explanation import export_receipt_proof_graph
from comp.persistence.codec import commit_receipt_to_body, encode_persistence_json
from comp.persistence.replay import ProjectionReplayReport
from comp.explanation.receipt_graph_cli import main
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)
from comp.persistence import replay_public_projection


def test_receipt_body_codec_is_backend_neutral():
    from comp.persistence.codec import (
        commit_receipt_from_body,
        commit_receipt_to_body,
    )

    case = receipt_projection_case(amount=100)
    body = commit_receipt_to_body(case.receipt)
    roundtripped = commit_receipt_from_body(body)

    assert roundtripped == case.receipt


def test_receipt_graph_cli_does_not_import_mysql_backend():
    source = Path("comp/explanation/receipt_graph_cli.py").read_text(encoding="utf-8")

    assert "comp.persistence.mysql" not in source


def test_scenario_contract_runtime_case_does_not_import_mysql_backend():
    source = Path("comp/scenario_contracts/case.py").read_text(encoding="utf-8")

    assert "comp.persistence.mysql" not in source


def test_receipt_graph_cli_exports_graph_json_from_replay_inputs(tmp_path, capsys):
    case = receipt_projection_case(amount=100, site="plant-a")
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )
    receipt_path = tmp_path / "receipt.json"
    replay_path = tmp_path / "replay.json"
    artifacts_path = tmp_path / "artifacts.json"

    receipt_path.write_text(
        json.dumps(commit_receipt_to_body(case.receipt), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    replay_path.write_text(
        json.dumps(_replay_payload(replay), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    artifacts_path.write_text(
        json.dumps(
            {"artifacts": [_artifact_payload(item) for item in artifacts.envelopes()]},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "export-json",
            "--receipt",
            str(receipt_path),
            "--replay",
            str(replay_path),
            "--artifacts",
            str(artifacts_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["authority"] == "explanation_only"
    assert payload["can_authorize_public_projection"] is False
    assert payload["public_row_id"] == case.receipt.public_row_id
    assert "plant-a" not in captured.out
    assert not _payload_has_key(payload, "value")


def test_receipt_graph_cli_can_write_graph_json_to_file(tmp_path, capsys):
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )
    receipt_path = tmp_path / "receipt.json"
    replay_path = tmp_path / "replay.json"
    artifacts_path = tmp_path / "artifacts.json"
    output_path = tmp_path / "graph.json"
    receipt_path.write_text(json.dumps(commit_receipt_to_body(case.receipt)), encoding="utf-8")
    replay_path.write_text(json.dumps(_replay_payload(replay)), encoding="utf-8")
    artifacts_path.write_text(
        json.dumps({"artifacts": [_artifact_payload(item) for item in artifacts.envelopes()]}),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "export-json",
            "--receipt",
            str(receipt_path),
            "--replay",
            str(replay_path),
            "--artifacts",
            str(artifacts_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert captured.out == ""
    assert payload["authority"] == "explanation_only"


def test_receipt_graph_cli_exports_mermaid_from_replay_inputs(tmp_path, capsys):
    receipt_path, replay_path, artifacts_path = _write_graph_inputs(
        tmp_path,
        site="plant-a",
    )

    exit_code = main(
        [
            "export-mermaid",
            "--receipt",
            str(receipt_path),
            "--replay",
            str(replay_path),
            "--artifacts",
            str(artifacts_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.startswith("flowchart TD\n")
    assert "-- \"authorized_by\" -->" in captured.out
    assert "plant-a" not in captured.out
    assert "value" not in captured.out


def test_receipt_graph_cli_exports_graphviz_dot_to_file(tmp_path, capsys):
    receipt_path, replay_path, artifacts_path = _write_graph_inputs(
        tmp_path,
        site="plant-a",
    )
    output_path = tmp_path / "graph.dot"

    exit_code = main(
        [
            "export-dot",
            "--receipt",
            str(receipt_path),
            "--replay",
            str(replay_path),
            "--artifacts",
            str(artifacts_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    output = output_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert captured.out == ""
    assert output.startswith("digraph ReceiptProofGraph {\n")
    assert "[label=\"authorized_by\"]" in output
    assert "plant-a" not in output
    assert "value" not in output


def test_receipt_graph_cli_renders_mermaid_from_scenario_proof_graph_payload(
    tmp_path,
    capsys,
):
    graph_payload = _sample_graph_payload(site="plant-a")
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(
        json.dumps({"scenario_id": "synthetic.demo", "proof_graph": graph_payload}),
        encoding="utf-8",
    )

    exit_code = main(["render-mermaid", "--graph", str(scenario_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("flowchart TD\n")
    assert "-- \"authorized_by\" -->" in captured.out
    assert "plant-a" not in captured.out


def test_receipt_graph_cli_renders_graphviz_dot_from_graph_payload_file(
    tmp_path,
    capsys,
):
    graph_path = tmp_path / "proof-graph.json"
    graph_path.write_text(
        json.dumps(_sample_graph_payload(site="plant-a")),
        encoding="utf-8",
    )

    exit_code = main(["render-dot", "--graph", str(graph_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("digraph ReceiptProofGraph {\n")
    assert "[label=\"authorized_by\"]" in captured.out
    assert "plant-a" not in captured.out


def test_receipt_graph_cli_reads_utf16_json_from_windows_redirect(
    tmp_path,
    capsys,
):
    scenario_path = tmp_path / "scenario.json"
    scenario_path.write_text(
        json.dumps(
            {
                "scenario_id": "synthetic.demo",
                "proof_graph": _sample_graph_payload(site="plant-a"),
            }
        ),
        encoding="utf-16",
    )

    exit_code = main(["render-mermaid", "--graph", str(scenario_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("flowchart TD\n")
    assert "plant-a" not in captured.out


def _sample_graph_payload(*, site: str = "plant-a") -> dict[str, object]:
    case = receipt_projection_case(amount=100, site=site)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )
    graph = export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )
    return graph.to_payload()


def _write_graph_inputs(tmp_path, *, site: str = "plant-a"):
    case = receipt_projection_case(amount=100, site=site)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )
    receipt_path = tmp_path / "receipt.json"
    replay_path = tmp_path / "replay.json"
    artifacts_path = tmp_path / "artifacts.json"
    receipt_path.write_text(
        json.dumps(commit_receipt_to_body(case.receipt)),
        encoding="utf-8",
    )
    replay_path.write_text(json.dumps(_replay_payload(replay)), encoding="utf-8")
    artifacts_path.write_text(
        json.dumps(
            {"artifacts": [_artifact_payload(item) for item in artifacts.envelopes()]}
        ),
        encoding="utf-8",
    )
    return receipt_path, replay_path, artifacts_path


def _replay_payload(replay: ProjectionReplayReport) -> dict[str, object]:
    return {
        "receipt_key": {
            "public_row_id": replay.receipt_key.public_row_id,
            "projection_id": replay.receipt_key.projection_id,
            "draft_id": replay.receipt_key.draft_id,
        },
        "projection_id": replay.projection_id,
        "public_row": replay.public_row,
        "artifact_refs": [
            {
                "artifact_id": ref.artifact_id,
                "artifact_kind": ref.artifact_kind,
            }
            for ref in replay.artifact_refs
        ],
        "artifact_digests": replay.artifact_digests,
        "dependency_fingerprints": [
            {
                "dependency_kind": fingerprint.dependency_kind,
                "dependency_id": fingerprint.dependency_id,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
            }
            for fingerprint in replay.dependency_fingerprints
        ],
    }


def _artifact_payload(envelope) -> dict[str, object]:
    return {
        "artifact_id": envelope.artifact_id,
        "artifact_kind": envelope.artifact_kind,
        "schema_version": envelope.schema_version,
        "body_digest": envelope.body_digest,
        "body": encode_persistence_json(envelope.body),
        "source_refs": encode_persistence_json(envelope.source_refs),
        "meta": encode_persistence_json(envelope.meta),
    }


def _payload_has_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_payload_has_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_payload_has_key(item, key) for item in value)
    return False
