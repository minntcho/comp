from dataclasses import replace

import pytest

from comp.persistence import ArtifactConflict, ReceiptConflict
from comp.persistence.codec import (
    commit_receipt_to_body,
    encode_persistence_json,
)
from comp.persistence.mysql import (
    TRUST_SPINE_SCHEMA_STATEMENTS,
    MySQLArtifactStore,
    MySQLReceiptLedger,
    apply_trust_spine_schema,
)
from tests.support.persistence_cases import claim_envelope, receipt_projection_case


class RecordingConnection:
    def __init__(self):
        self.executed = []
        self.commits = 0

    def cursor(self):
        return RecordingCursor(self)

    def commit(self):
        self.commits += 1


class RecordingCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, statement, params=None):
        self.connection.executed.append((statement, params))


def test_trust_spine_schema_setup_uses_idempotent_ddl_and_single_commit():
    connection = RecordingConnection()

    apply_trust_spine_schema(connection)

    assert connection.commits == 1
    assert [statement for statement, _ in connection.executed] == list(
        TRUST_SPINE_SCHEMA_STATEMENTS
    )
    assert all(
        "create table if not exists" in statement.lower()
        for statement in TRUST_SPINE_SCHEMA_STATEMENTS
    )


def test_trust_spine_indexes_are_receipt_derived_not_independent_authority():
    schema = "\n".join(TRUST_SPINE_SCHEMA_STATEMENTS).lower()

    assert "ledger_commit_receipts" in schema
    for table in (
        "ledger_receipt_value_commitments",
        "ledger_receipt_dependency_fingerprints",
        "ledger_receipt_artifact_refs",
    ):
        assert f"create table if not exists {table}" in schema

    assert schema.count(
        "foreign key (receipt_id) references ledger_commit_receipts(receipt_id)"
    ) == 3


def test_artifact_duplicate_key_rechecks_existing_envelope():
    envelope = claim_envelope(value=1200)
    connection = SequencedConnection(
        select_rows=[_artifact_row(envelope)],
        failures=[InsertFailure("artifact_envelopes", DuplicateKeyError())],
    )

    recorded = MySQLArtifactStore(connection).record(envelope)

    assert recorded == envelope
    assert connection.rollbacks == 1
    assert connection.commits == 0


def test_artifact_duplicate_key_conflict_raises_domain_error():
    existing = claim_envelope(value=1200)
    incoming = claim_envelope(value=1201)
    connection = SequencedConnection(
        select_rows=[_artifact_row(existing)],
        failures=[InsertFailure("artifact_envelopes", DuplicateKeyError())],
    )

    with pytest.raises(ArtifactConflict, match="artifact:claim:1"):
        MySQLArtifactStore(connection).record(incoming)

    assert connection.rollbacks == 1
    assert connection.commits == 0


def test_receipt_duplicate_key_conflict_raises_domain_error():
    receipt = receipt_projection_case(amount=100).receipt
    changed = replace(receipt, authorized_fields=("site",))
    connection = SequencedConnection(
        select_rows=[_receipt_row(receipt)],
        failures=[InsertFailure("ledger_commit_receipts", DuplicateKeyError())],
    )

    with pytest.raises(ReceiptConflict, match="public-row-1"):
        MySQLReceiptLedger(connection).record(changed)

    assert connection.rollbacks == 1
    assert connection.commits == 0


def test_receipt_index_insert_failure_rolls_back_root_transaction():
    receipt = receipt_projection_case(amount=100).receipt
    connection = SequencedConnection(
        select_rows=[None],
        failures=[
            InsertFailure(
                "ledger_receipt_value_commitments",
                IndexInsertError("index insert failed"),
            )
        ],
    )

    with pytest.raises(IndexInsertError):
        MySQLReceiptLedger(connection).record(receipt)

    assert connection.rollbacks == 1
    assert connection.commits == 0


class DuplicateKeyError(Exception):
    def __init__(self):
        super().__init__(1062, "Duplicate entry")


class IndexInsertError(Exception):
    pass


class InsertFailure:
    def __init__(self, table: str, error: Exception):
        self.table = table
        self.error = error


class SequencedConnection:
    def __init__(self, *, select_rows, failures):
        self.select_rows = list(select_rows)
        self.failures = list(failures)
        self.executed = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return SequencedCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class SequencedCursor:
    def __init__(self, connection):
        self.connection = connection
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, statement, params=None):
        self.connection.executed.append((statement, params))
        normalized = " ".join(statement.lower().split())
        if normalized.startswith("select "):
            self._row = self.connection.select_rows.pop(0)
            return
        for index, failure in enumerate(self.connection.failures):
            if f"insert into {failure.table}" in normalized:
                self.connection.failures.pop(index)
                raise failure.error

    def fetchone(self):
        return self._row

    def fetchall(self):
        return ()


def _artifact_row(envelope):
    return (
        envelope.artifact_id,
        envelope.artifact_kind,
        envelope.schema_version,
        envelope.body_digest,
        _json_dump(encode_persistence_json(envelope.body)),
        _json_dump(encode_persistence_json(envelope.source_refs)),
        _json_dump(encode_persistence_json(envelope.meta)),
    )


def _receipt_row(receipt):
    return (_json_dump(encode_persistence_json(commit_receipt_to_body(receipt))),)


def _json_dump(value):
    import json

    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
