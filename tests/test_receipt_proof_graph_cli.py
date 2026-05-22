import json

from comp.persistence.mysql import commit_receipt_to_body
from comp.persistence.codec import encode_persistence_json
from comp.persistence.replay import ProjectionReplayReport
from comp.explanation.receipt_graph_cli import main
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)
from comp.persistence import replay_public_projection


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
