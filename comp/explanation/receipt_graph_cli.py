from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from comp.explanation import export_receipt_proof_graph
from comp.judgment import DependencyFingerprint
from comp.persistence import (
    ArtifactEnvelope,
    ArtifactRef,
    InMemoryArtifactStore,
    ProjectionReplayReport,
    ReceiptLedgerKey,
)
from comp.persistence.codec import decode_persistence_json
from comp.persistence.mysql import commit_receipt_from_body


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "export-json":
        graph = export_receipt_proof_graph(
            receipt=commit_receipt_from_body(_load_mapping(args.receipt)),
            replay=_replay_from_payload(_load_mapping(args.replay)),
            artifacts=_artifact_store_from_payload(_load_mapping(args.artifacts)),
        )
        output = graph.to_json() + "\n"
        if args.output is None:
            sys.stdout.write(output)
        else:
            Path(args.output).write_text(output, encoding="utf-8")
        return 0

    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="comp-receipt-graph",
        description="Export receipt proof graphs as explanation-only JSON.",
    )
    subparsers = parser.add_subparsers(dest="command")
    export = subparsers.add_parser(
        "export-json",
        help="Export a ReceiptProofGraph from receipt, replay, and artifact JSON.",
    )
    export.add_argument("--receipt", required=True, help="CommitReceipt body JSON path.")
    export.add_argument("--replay", required=True, help="ProjectionReplayReport JSON path.")
    export.add_argument(
        "--artifacts",
        required=True,
        help="JSON path containing an artifacts array of ArtifactEnvelope payloads.",
    )
    export.add_argument(
        "--output",
        help="Optional output JSON path. Defaults to stdout.",
    )
    return parser


def _load_mapping(path: str) -> Mapping[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and "__comp_type__" in payload:
        payload = decode_persistence_json(payload)
    if not isinstance(payload, Mapping):
        raise TypeError(f"Expected JSON object: {path}.")
    return payload


def _replay_from_payload(payload: Mapping[str, Any]) -> ProjectionReplayReport:
    receipt_key = _mapping(payload["receipt_key"], "receipt_key")
    return ProjectionReplayReport(
        receipt_key=ReceiptLedgerKey(
            public_row_id=str(receipt_key["public_row_id"]),
            projection_id=str(receipt_key["projection_id"]),
            draft_id=str(receipt_key["draft_id"]),
        ),
        projection_id=str(payload["projection_id"]),
        public_row=dict(_mapping(payload["public_row"], "public_row")),
        artifact_refs=tuple(
            ArtifactRef(
                artifact_id=str(_mapping(item, "artifact_ref")["artifact_id"]),
                artifact_kind=str(_mapping(item, "artifact_ref")["artifact_kind"]),
            )
            for item in _sequence(payload["artifact_refs"], "artifact_refs")
        ),
        artifact_digests=tuple(
            (str(item[0]), str(item[1]))
            for item in _sequence(payload["artifact_digests"], "artifact_digests")
        ),
        dependency_fingerprints=tuple(
            _dependency_fingerprint_from_payload(item)
            for item in _sequence(
                payload.get("dependency_fingerprints", ()),
                "dependency_fingerprints",
            )
        ),
    )


def _artifact_store_from_payload(payload: Mapping[str, Any]) -> InMemoryArtifactStore:
    store = InMemoryArtifactStore()
    for item in _sequence(payload["artifacts"], "artifacts"):
        envelope_payload = _mapping(item, "artifact")
        store.record(
            ArtifactEnvelope(
                artifact_id=str(envelope_payload["artifact_id"]),
                artifact_kind=str(envelope_payload["artifact_kind"]),
                schema_version=str(envelope_payload["schema_version"]),
                body_digest=str(envelope_payload["body_digest"]),
                body=_decode_field_mapping(envelope_payload["body"], "artifact.body"),
                source_refs=tuple(
                    _decode_field(envelope_payload.get("source_refs", ()))
                ),
                meta=tuple(_decode_field(envelope_payload.get("meta", ()))),
            )
        )
    return store


def _dependency_fingerprint_from_payload(value: Any) -> DependencyFingerprint:
    payload = _mapping(value, "dependency_fingerprint")
    return DependencyFingerprint(
        dependency_kind=str(payload["dependency_kind"]),
        dependency_id=str(payload["dependency_id"]),
        fingerprint=str(payload["fingerprint"]),
        digest_alg=str(payload.get("digest_alg", "sha256")),
    )


def _decode_field(value: Any) -> Any:
    if isinstance(value, Mapping) and "__comp_type__" in value:
        return decode_persistence_json(value)
    return value


def _decode_field_mapping(value: Any, name: str) -> Mapping[str, Any]:
    decoded = _decode_field(value)
    return _mapping(decoded, name)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected object for {name}.")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"Expected array for {name}.")
    return value


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
