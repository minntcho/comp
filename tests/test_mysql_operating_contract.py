from comp.persistence.mysql import (
    TRUST_SPINE_SCHEMA_STATEMENTS,
    apply_trust_spine_schema,
)


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
