import os
from dataclasses import replace
from decimal import Decimal
from typing import get_type_hints

import pytest

from comp.persistence import (
    ArtifactConflict,
    ArtifactEnvelope,
    ArtifactIntegrityError,
    ReceiptConflict,
    receipt_artifact_refs,
    replay_public_projection,
    verify_artifact_envelope,
)
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    claim_envelope,
    receipt_projection_case,
)


pytestmark = pytest.mark.mysql


def _database_config() -> dict[str, object]:
    host = os.environ.get("COMP_TEST_MYSQL_HOST")
    if not host:
        pytest.skip("COMP_TEST_MYSQL_HOST is required for MySQL spine tests")
    return {
        "host": host,
        "port": int(os.environ.get("COMP_TEST_MYSQL_PORT", "3306")),
        "user": os.environ.get("COMP_TEST_MYSQL_USER", "comp"),
        "password": os.environ.get("COMP_TEST_MYSQL_PASSWORD", "comp"),
        "database": os.environ.get("COMP_TEST_MYSQL_DATABASE", "comp_test"),
        "charset": "utf8mb4",
        "autocommit": False,
    }


def _connect_mysql():
    pymysql = pytest.importorskip("pymysql")
    return pymysql.connect(**_database_config())


def _reset_spine(connection):
    with connection.cursor() as cursor:
        cursor.execute("set foreign_key_checks = 0")
        for table in (
            "ledger_receipt_artifact_refs",
            "ledger_receipt_dependency_fingerprints",
            "ledger_receipt_value_commitments",
            "ledger_commit_receipts",
            "artifact_envelopes",
        ):
            cursor.execute(f"truncate table {table}")
        cursor.execute("set foreign_key_checks = 1")
    connection.commit()


def test_mysql_spine_module_exists():
    from comp.persistence.mysql import apply_trust_spine_schema

    assert apply_trust_spine_schema is not None


def test_mysql_artifact_store_satisfies_graph_export_artifact_store_protocol():
    from comp.explanation import export_receipt_proof_graph
    from comp.persistence import ArtifactStore
    from comp.persistence.mysql import MySQLArtifactStore

    hints = get_type_hints(export_receipt_proof_graph)

    assert hints["artifacts"] is ArtifactStore
    assert isinstance(MySQLArtifactStore(object()), ArtifactStore)


def test_persistence_codec_roundtrips_tuple_and_decimal_body():
    from comp.persistence.codec import decode_persistence_json, encode_persistence_json

    envelope = ArtifactEnvelope.from_body(
        artifact_id="artifact:codec:1",
        artifact_kind="codec_fixture",
        schema_version="v1",
        body={
            "tuple_value": ("a", "b"),
            "list_value": ["a", "b"],
            "decimal_value": Decimal("1.25"),
        },
    )

    encoded = encode_persistence_json(envelope.body)
    decoded = decode_persistence_json(encoded)

    assert decoded == envelope.body
    assert isinstance(decoded["tuple_value"], tuple)
    assert isinstance(decoded["list_value"], list)
    assert isinstance(decoded["decimal_value"], Decimal)

    roundtripped = ArtifactEnvelope(
        artifact_id=envelope.artifact_id,
        artifact_kind=envelope.artifact_kind,
        schema_version=envelope.schema_version,
        body_digest=envelope.body_digest,
        body=decoded,
        source_refs=envelope.source_refs,
        meta=envelope.meta,
    )
    verify_artifact_envelope(roundtripped)


def test_apply_trust_spine_schema_creates_v1_tables():
    pymysql = pytest.importorskip("pymysql")
    from comp.persistence.mysql import apply_trust_spine_schema

    connection = pymysql.connect(**_database_config())
    try:
        apply_trust_spine_schema(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = database()
                order by table_name
                """
            )
            tables = {row[0] for row in cursor.fetchall()}
    finally:
        connection.close()

    assert "artifact_envelopes" in tables
    assert "ledger_commit_receipts" in tables
    assert "ledger_receipt_value_commitments" in tables
    assert "ledger_receipt_dependency_fingerprints" in tables
    assert "ledger_receipt_artifact_refs" in tables


def test_mysql_artifact_store_records_envelopes_idempotently():
    from comp.persistence.mysql import MySQLArtifactStore, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        store = MySQLArtifactStore(connection)
        envelope = claim_envelope(value=1200)

        assert store.record(envelope) == envelope
        assert store.record(envelope) == envelope
        assert store.get("artifact:claim:1") == envelope
        assert store.envelopes() == (envelope,)
    finally:
        connection.close()


def test_mysql_artifact_store_rejects_conflicting_content():
    from comp.persistence.mysql import MySQLArtifactStore, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        store = MySQLArtifactStore(connection)
        store.record(claim_envelope(value=1200))

        with pytest.raises(ArtifactConflict, match="artifact:claim:1"):
            store.record(claim_envelope(value=1201))
    finally:
        connection.close()


def test_mysql_artifact_store_rejects_invalid_digest():
    from comp.persistence.mysql import MySQLArtifactStore, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        store = MySQLArtifactStore(connection)
        envelope = claim_envelope(value=1200)
        tampered = replace(envelope, body={"field": "amount", "value": 999})

        with pytest.raises(ArtifactIntegrityError, match="body digest"):
            store.record(tampered)
    finally:
        connection.close()


def test_mysql_receipt_ledger_records_receipts_idempotently():
    from comp.persistence.mysql import MySQLReceiptLedger, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        ledger = MySQLReceiptLedger(connection)
        receipt = receipt_projection_case(amount=100).receipt

        assert ledger.record(receipt) == receipt
        assert ledger.record(receipt) == receipt
        assert ledger.get(
            public_row_id="public-row-1",
            projection_id="public-row",
            draft_id="draft-1",
        ) == receipt
        assert ledger.receipts() == (receipt,)
    finally:
        connection.close()


def test_mysql_receipt_ledger_rejects_conflicting_receipt_root():
    from comp.persistence.mysql import MySQLReceiptLedger, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        ledger = MySQLReceiptLedger(connection)
        receipt = receipt_projection_case(amount=100).receipt
        changed = replace(receipt, authorized_fields=("site",))

        ledger.record(receipt)
        with pytest.raises(ReceiptConflict, match="public-row-1"):
            ledger.record(changed)
    finally:
        connection.close()


def test_mysql_receipt_ledger_populates_receipt_indexes():
    from comp.persistence.mysql import MySQLReceiptLedger, apply_trust_spine_schema

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        receipt = receipt_projection_case(amount=100).receipt
        ledger = MySQLReceiptLedger(connection)
        ledger.record(receipt)

        with connection.cursor() as cursor:
            cursor.execute("select count(*) from ledger_receipt_value_commitments")
            value_commitments = cursor.fetchone()[0]
            cursor.execute("select count(*) from ledger_receipt_dependency_fingerprints")
            dependencies = cursor.fetchone()[0]
            cursor.execute("select count(*) from ledger_receipt_artifact_refs")
            refs = cursor.fetchone()[0]
    finally:
        connection.close()

    assert receipt.citations is not None
    assert value_commitments == len(receipt.citations.projection_value_commitments)
    assert dependencies == len(receipt.citations.dependency_fingerprints)
    assert refs == len(set(receipt_artifact_refs(receipt)))


def test_mysql_artifact_store_supports_replay_public_projection():
    from comp.persistence.mysql import MySQLArtifactStore, apply_trust_spine_schema

    case = receipt_projection_case(amount=100)
    memory_store = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        mysql_store = MySQLArtifactStore(connection)
        for envelope in memory_store.envelopes():
            mysql_store.record(envelope)

        report = replay_public_projection(
            case.source_values,
            case.projection,
            receipt=case.receipt,
            artifacts=mysql_store,
        )
    finally:
        connection.close()

    assert report.public_row == case.public_row
    assert report.artifact_refs == receipt_artifact_refs(case.receipt)


def test_mysql_spine_supports_replay_then_receipt_proof_graph_export():
    from comp.explanation import export_receipt_proof_graph
    from comp.persistence.mysql import (
        MySQLArtifactStore,
        MySQLReceiptLedger,
        apply_trust_spine_schema,
    )

    case = receipt_projection_case(amount=100, site="plant-a")
    memory_store = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )

    connection = _connect_mysql()
    try:
        apply_trust_spine_schema(connection)
        _reset_spine(connection)
        mysql_store = MySQLArtifactStore(connection)
        mysql_ledger = MySQLReceiptLedger(connection)
        for envelope in memory_store.envelopes():
            mysql_store.record(envelope)
        mysql_ledger.record(case.receipt)

        persisted_receipt = mysql_ledger.get(
            public_row_id=case.receipt.public_row_id,
            projection_id=case.receipt.projection_id,
            draft_id=case.receipt.draft_id,
        )
        replay = replay_public_projection(
            case.source_values,
            case.projection,
            receipt=persisted_receipt,
            artifacts=mysql_store,
        )
        graph = export_receipt_proof_graph(
            receipt=persisted_receipt,
            replay=replay,
            artifacts=mysql_store,
        )
    finally:
        connection.close()

    payload = graph.to_payload()
    node_kinds = {node["node_kind"] for node in payload["nodes"]}
    edge_kinds = {edge["edge_kind"] for edge in payload["edges"]}

    assert replay.public_row == case.public_row
    assert graph.authority == "explanation_only"
    assert graph.can_authorize_public_projection is False
    assert graph.replay_receipt_key.public_row_id == case.receipt.public_row_id
    assert {
        "commit_receipt",
        "public_projection",
        "dependency_fingerprint",
    } <= node_kinds
    assert {"authorized_by", "pinned_dependency", "projected_as"} <= edge_kinds
    assert "plant-a" not in repr(payload)
    assert not _payload_has_key(payload, "value")


def _payload_has_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(
            _payload_has_key(item, key) for item in value.values()
        )
    if isinstance(value, (tuple, list)):
        return any(_payload_has_key(item, key) for item in value)
    return False
