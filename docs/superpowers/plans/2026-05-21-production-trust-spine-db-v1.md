# MySQL Trust Spine DB V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real MySQL-backed durable persistence spine for artifact envelopes and commit receipts without expanding into workflow UI, registry admin, projection caches, or domain-specific indexes yet.

**Architecture:** V1 keeps the existing in-memory persistence contract as the behavioral source of truth and adds a MySQL backend that implements the same artifact-store and receipt-ledger semantics. The first durable spine records immutable artifact envelopes, append-only commit receipts, and receipt-derived query indexes in one transaction while preserving replay compatibility.

**Tech Stack:** Python 3.11, MySQL 8.4, PyMySQL, pytest, GitHub Actions MySQL service.

---

## Scope

Implement only the minimum durable spine:

```text
artifact_envelopes
ledger_commit_receipts
ledger_receipt_value_commitments
ledger_receipt_dependency_fingerprints
ledger_receipt_artifact_refs
```

Do not implement these in V1:

```text
workflow_cases
workflow_source_units
workflow_source_spans
workflow_resolver_tasks
registry_domain_packs
registry_compiler_profiles
registry_reference_catalog_versions
projection_public_projection_versions
typed artifact indexes
domain-specific views
```

Reason: V1 should prove that persisted artifacts and receipts can replay the
same authority path as the in-memory substrate. Workflow, registry, and
projection tables can follow once this spine is trustworthy.

## MySQL Design Notes

The database north-star uses logical schemas such as `artifact` and `ledger`.
MySQL V1 should use one database and table prefixes instead:

```text
artifact.artifact_envelopes -> artifact_envelopes
ledger.commit_receipts -> ledger_commit_receipts
```

Do not split V1 into multiple MySQL databases. One database keeps transaction
boundaries straightforward and avoids cross-database permission complexity.

MySQL `JSON` is a storage type, not the source of digest truth. All artifact and
receipt bodies must pass through a Python persistence codec before storage and
after loading:

```text
Python value -> encode_persistence_json -> MySQL JSON
MySQL JSON -> decode_persistence_json -> Python value
```

This preserves tuple/list and Decimal distinctions that existing digest
semantics depend on.

## File Structure

Create:

```text
comp/persistence/mysql.py
  MySQLArtifactStore, MySQLReceiptLedger, schema application, and SQL statements
  for V1 tables.

comp/persistence/codec.py
  Persistence JSON codec that preserves Python values needed by existing digest
  semantics, especially tuple/list distinction and Decimal values.

tests/test_mysql_persistence_spine.py
  MySQL integration tests for artifact idempotency, conflicts, receipt indexes,
  and replay.
```

Modify:

```text
comp/persistence/__init__.py
  Export MySQL store/ledger classes behind the optional db dependency.

pyproject.toml
  Add optional `db` dependency for PyMySQL.

.github/workflows/ci.yml
  Add a MySQL service and install `.[test,db]` so DB tests run in CI.

docs/architecture/production-trust-spine-database.md
  Update current implementation status after the V1 backend exists.
```

## Design Rules

1. `MySQLArtifactStore.record()` must behave like `InMemoryArtifactStore.record()`.
2. `MySQLReceiptLedger.record()` must behave like `InMemoryReceiptLedger.record()`.
3. Same artifact id and same digest is idempotent.
4. Same artifact id with different kind, schema, or digest raises `ArtifactConflict`.
5. Same receipt ledger key and same receipt body is idempotent.
6. Same receipt ledger key with different receipt body raises `ReceiptConflict`.
7. Receipt-derived tables are indexes, not a second source of truth.
8. Replay must work through `replay_public_projection(row, projection, receipt=receipt, artifacts=mysql_store)`.
9. JSON roundtrip must not change `artifact_digest` semantics.
10. Avoid MySQL upserts for authority-bearing rows; read first, compare, then insert.

The last two rules matter because MySQL JSON cannot distinguish tuple from list
by itself, and blind upserts can accidentally blur immutable conflict behavior.

---

### Task 1: Add MySQL Integration Test Harness

**Files:**
- Create: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write the failing fixture and skip policy**

Add this test file:

```python
import os

import pytest

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


def test_mysql_spine_module_exists():
    from comp.persistence.mysql import apply_trust_spine_schema

    assert apply_trust_spine_schema is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_mysql_persistence_spine.py::test_mysql_spine_module_exists -q
```

Expected:

```text
FAILED with ModuleNotFoundError: No module named 'comp.persistence.mysql'
```

- [ ] **Step 3: Commit RED test**

```bash
git add tests/test_mysql_persistence_spine.py
git commit -m "test: add mysql spine smoke test"
```

### Task 2: Add Optional DB Dependency And CI MySQL Service

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add `db` optional dependency**

Change optional dependencies to:

```toml
[project.optional-dependencies]
test = ["pytest>=8"]
db = ["PyMySQL>=1.1"]
```

- [ ] **Step 2: Add MySQL service to CI**

Update `.github/workflows/ci.yml`:

```yaml
jobs:
  contract:
    name: Python contract suite
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.4
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: comp_test
          MYSQL_USER: comp
          MYSQL_PASSWORD: comp
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping -h 127.0.0.1 -ucomp -pcomp"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=10
```

Change install and test steps:

```yaml
      - name: Install package
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[test,db]"

      - name: Run unit and scenario tests
        env:
          COMP_TEST_MYSQL_HOST: 127.0.0.1
          COMP_TEST_MYSQL_PORT: "3306"
          COMP_TEST_MYSQL_USER: comp
          COMP_TEST_MYSQL_PASSWORD: comp
          COMP_TEST_MYSQL_DATABASE: comp_test
        run: python -m pytest -q
```

- [ ] **Step 3: Run existing smoke tests locally**

Run:

```bash
python -m pytest tests/test_package_smoke.py -q
```

Expected:

```text
passed
```

- [ ] **Step 4: Commit dependency and CI setup**

```bash
git add pyproject.toml .github/workflows/ci.yml
git commit -m "ci: add mysql db test service"
```

### Task 3: Implement Persistence Codec

**Files:**
- Create: `comp/persistence/codec.py`
- Test: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write failing codec tests**

Append:

```python
from decimal import Decimal

from comp.persistence import ArtifactEnvelope, verify_artifact_envelope


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_mysql_persistence_spine.py::test_persistence_codec_roundtrips_tuple_and_decimal_body -q
```

Expected:

```text
FAILED with ModuleNotFoundError: No module named 'comp.persistence.codec'
```

- [ ] **Step 3: Implement codec**

Create `comp/persistence/codec.py`:

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any


def encode_persistence_json(value: Any) -> Any:
    if value is None:
        return {"__comp_type__": "none", "value": None}
    if isinstance(value, bool):
        return {"__comp_type__": "bool", "value": value}
    if isinstance(value, int):
        return {"__comp_type__": "int", "value": str(value)}
    if isinstance(value, float):
        return {"__comp_type__": "float", "value": repr(value)}
    if isinstance(value, str):
        return {"__comp_type__": "str", "value": value}
    if isinstance(value, Decimal):
        return {"__comp_type__": "decimal", "value": str(value)}
    if isinstance(value, Mapping):
        return {
            "__comp_type__": "mapping",
            "value": [
                [str(key), encode_persistence_json(item)]
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            ],
        }
    if isinstance(value, tuple):
        return {
            "__comp_type__": "tuple",
            "value": [encode_persistence_json(item) for item in value],
        }
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {
            "__comp_type__": "list",
            "value": [encode_persistence_json(item) for item in value],
        }
    raise TypeError(f"Unsupported persistence JSON value: {type(value).__name__}")


def decode_persistence_json(value: Any) -> Any:
    if not isinstance(value, Mapping) or "__comp_type__" not in value:
        raise TypeError("Persistence JSON value is missing __comp_type__")
    kind = value["__comp_type__"]
    raw = value["value"]
    if kind == "none":
        return None
    if kind == "bool":
        return bool(raw)
    if kind == "int":
        return int(raw)
    if kind == "float":
        return float(raw)
    if kind == "str":
        return str(raw)
    if kind == "decimal":
        return Decimal(str(raw))
    if kind == "mapping":
        return {str(key): decode_persistence_json(item) for key, item in raw}
    if kind == "tuple":
        return tuple(decode_persistence_json(item) for item in raw)
    if kind == "list":
        return [decode_persistence_json(item) for item in raw]
    raise TypeError(f"Unsupported persistence JSON type: {kind}")


__all__ = ["decode_persistence_json", "encode_persistence_json"]
```

- [ ] **Step 4: Run codec test**

```bash
python -m pytest tests/test_mysql_persistence_spine.py::test_persistence_codec_roundtrips_tuple_and_decimal_body -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit codec**

```bash
git add comp/persistence/codec.py tests/test_mysql_persistence_spine.py
git commit -m "feat: add persistence json codec"
```

### Task 4: Add MySQL Schema Application

**Files:**
- Create: `comp/persistence/mysql.py`
- Test: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write failing schema test**

Append:

```python
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
```

- [ ] **Step 2: Run schema test to verify it fails**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py::test_apply_trust_spine_schema_creates_v1_tables -q
```

Expected before implementation:

```text
FAILED with ImportError or AttributeError for apply_trust_spine_schema
```

- [ ] **Step 3: Implement `apply_trust_spine_schema`**

Create `comp/persistence/mysql.py`:

```python
from __future__ import annotations

from typing import Any


TRUST_SPINE_SCHEMA_STATEMENTS = (
    """
    create table if not exists artifact_envelopes (
      artifact_id varchar(255) primary key,
      artifact_kind varchar(128) not null,
      schema_version varchar(64) not null,
      body_digest varchar(96) not null,
      body json not null,
      source_refs json not null,
      meta json not null,
      created_at timestamp(6) not null default current_timestamp(6),
      unique key artifact_envelope_identity (
        artifact_id, artifact_kind, schema_version, body_digest
      )
    ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_0900_bin
    """,
    """
    create table if not exists ledger_commit_receipts (
      receipt_id varchar(255) primary key,
      public_row_id varchar(255) not null,
      projection_id varchar(255) not null,
      draft_id varchar(255) not null,
      receipt_digest varchar(96) not null,
      receipt_body json not null,
      issued_at timestamp(6) not null default current_timestamp(6),
      unique key receipt_ledger_key (public_row_id, projection_id, draft_id)
    ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_0900_bin
    """,
    """
    create table if not exists ledger_receipt_value_commitments (
      receipt_id varchar(255) not null,
      field varchar(255) not null,
      source_kind varchar(128) not null,
      source_id varchar(255) not null,
      value_digest varchar(96) not null,
      digest_alg varchar(32) not null,
      primary key (receipt_id, field),
      constraint fk_receipt_value_commitments_receipt
        foreign key (receipt_id) references ledger_commit_receipts(receipt_id)
    ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_0900_bin
    """,
    """
    create table if not exists ledger_receipt_dependency_fingerprints (
      receipt_id varchar(255) not null,
      dependency_kind varchar(128) not null,
      dependency_id varchar(255) not null,
      fingerprint varchar(96) not null,
      digest_alg varchar(32) not null,
      primary key (receipt_id, dependency_kind, dependency_id),
      constraint fk_receipt_dependency_fingerprints_receipt
        foreign key (receipt_id) references ledger_commit_receipts(receipt_id)
    ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_0900_bin
    """,
    """
    create table if not exists ledger_receipt_artifact_refs (
      receipt_id varchar(255) not null,
      artifact_id varchar(255) not null,
      artifact_kind varchar(128) not null,
      role varchar(128) not null,
      primary key (receipt_id, artifact_id, artifact_kind, role),
      constraint fk_receipt_artifact_refs_receipt
        foreign key (receipt_id) references ledger_commit_receipts(receipt_id)
    ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_0900_bin
    """,
)


def apply_trust_spine_schema(connection: Any) -> None:
    with connection.cursor() as cursor:
        for statement in TRUST_SPINE_SCHEMA_STATEMENTS:
            cursor.execute(statement)
    connection.commit()
```

- [ ] **Step 4: Run schema test**

Use the command from Step 2.

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit schema**

```bash
git add comp/persistence/mysql.py tests/test_mysql_persistence_spine.py
git commit -m "feat: add mysql trust spine schema"
```

### Task 5: Implement MySQLArtifactStore

**Files:**
- Modify: `comp/persistence/mysql.py`
- Test: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write failing artifact store tests**

Append:

```python
from dataclasses import replace

from comp.persistence import ArtifactConflict, ArtifactIntegrityError
from tests.support.persistence_cases import claim_envelope


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
```

- [ ] **Step 2: Run artifact tests to verify they fail**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py::test_mysql_artifact_store_records_envelopes_idempotently tests/test_mysql_persistence_spine.py::test_mysql_artifact_store_rejects_conflicting_content tests/test_mysql_persistence_spine.py::test_mysql_artifact_store_rejects_invalid_digest -q
```

Expected:

```text
FAILED with ImportError or AttributeError for MySQLArtifactStore
```

- [ ] **Step 3: Implement `MySQLArtifactStore`**

Add imports to `comp/persistence/mysql.py`:

```python
import json

from comp.persistence.codec import decode_persistence_json, encode_persistence_json
from comp.persistence.envelope import ArtifactEnvelope
from comp.persistence.ledger import ArtifactConflict, verify_artifact_envelope
```

Add helpers:

```python
def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _json_load(value: str | bytes | bytearray) -> Any:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    return json.loads(value)
```

Add class:

```python
class MySQLArtifactStore:
    def __init__(self, connection: Any):
        self.connection = connection

    def record(self, envelope: ArtifactEnvelope) -> ArtifactEnvelope:
        verify_artifact_envelope(envelope)
        existing = self._get_optional(envelope.artifact_id)
        if existing is None:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into artifact_envelopes (
                      artifact_id, artifact_kind, schema_version, body_digest,
                      body, source_refs, meta
                    )
                    values (%s, %s, %s, %s, cast(%s as json), cast(%s as json), cast(%s as json))
                    """,
                    (
                        envelope.artifact_id,
                        envelope.artifact_kind,
                        envelope.schema_version,
                        envelope.body_digest,
                        _json_dump(encode_persistence_json(envelope.body)),
                        _json_dump(encode_persistence_json(envelope.source_refs)),
                        _json_dump(encode_persistence_json(envelope.meta)),
                    ),
                )
            self.connection.commit()
            return envelope
        if (
            existing.artifact_kind != envelope.artifact_kind
            or existing.schema_version != envelope.schema_version
            or existing.body_digest != envelope.body_digest
        ):
            raise ArtifactConflict(
                f"Artifact already recorded with different content: "
                f"{envelope.artifact_id}."
            )
        return existing

    def get(self, artifact_id: str) -> ArtifactEnvelope:
        existing = self._get_optional(artifact_id)
        if existing is None:
            raise KeyError(artifact_id)
        return existing

    def envelopes(self) -> tuple[ArtifactEnvelope, ...]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select artifact_id, artifact_kind, schema_version, body_digest,
                       body, source_refs, meta
                from artifact_envelopes
                order by artifact_id
                """
            )
            return tuple(_artifact_envelope_from_row(row) for row in cursor.fetchall())

    def _get_optional(self, artifact_id: str) -> ArtifactEnvelope | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select artifact_id, artifact_kind, schema_version, body_digest,
                       body, source_refs, meta
                from artifact_envelopes
                where artifact_id = %s
                """,
                (artifact_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return _artifact_envelope_from_row(row)


def _artifact_envelope_from_row(row) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_id=row[0],
        artifact_kind=row[1],
        schema_version=row[2],
        body_digest=row[3],
        body=decode_persistence_json(_json_load(row[4])),
        source_refs=decode_persistence_json(_json_load(row[5])),
        meta=decode_persistence_json(_json_load(row[6])),
    )
```

- [ ] **Step 4: Run artifact store tests**

Use the command from Step 2.

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit artifact store**

```bash
git add comp/persistence/mysql.py tests/test_mysql_persistence_spine.py
git commit -m "feat: add mysql artifact store"
```

### Task 6: Implement CommitReceipt Serialization And Ledger

**Files:**
- Modify: `comp/persistence/mysql.py`
- Test: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write failing receipt ledger tests**

Append:

```python
from comp.persistence import ReceiptConflict
from tests.support.persistence_cases import receipt_projection_case


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
```

- [ ] **Step 2: Run receipt tests to verify they fail**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py::test_mysql_receipt_ledger_records_receipts_idempotently tests/test_mysql_persistence_spine.py::test_mysql_receipt_ledger_rejects_conflicting_receipt_root -q
```

Expected:

```text
FAILED with ImportError or AttributeError for MySQLReceiptLedger
```

- [ ] **Step 3: Implement serialization helpers**

In `comp/persistence/mysql.py`, add helper functions:

```python
import hashlib

from comp.judgment.receipts import (
    CommitReceipt,
    CommitReceiptCitations,
    DependencyFingerprint,
    ProjectionValueCommitment,
)
from comp.persistence.ledger import ReceiptConflict, ReceiptLedgerKey
from comp.persistence.replay import receipt_artifact_refs


def receipt_id(receipt: CommitReceipt) -> str:
    body = commit_receipt_to_body(receipt)
    canonical = json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "receipt:sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def commit_receipt_to_body(receipt: CommitReceipt) -> dict[str, Any]:
    citations = None
    if receipt.citations is not None:
        citations = {
            "governance_decision_id": receipt.citations.governance_decision_id,
            "governance_status": receipt.citations.governance_status,
            "governance_reasons": receipt.citations.governance_reasons,
            "commit_package_id": receipt.citations.commit_package_id,
            "commit_package_complete": receipt.citations.commit_package_complete,
            "subject_id": receipt.citations.subject_id,
            "projection_id": receipt.citations.projection_id,
            "authorized_fields": receipt.citations.authorized_fields,
            "profile_id": receipt.citations.profile_id,
            "report_status": receipt.citations.report_status,
            "checked_claim_fields": receipt.citations.checked_claim_fields,
            "checked_claim_witness_ids": receipt.citations.checked_claim_witness_ids,
            "semantic_judgment_ids": receipt.citations.semantic_judgment_ids,
            "reference_binding_ids": receipt.citations.reference_binding_ids,
            "derived_claim_fields": receipt.citations.derived_claim_fields,
            "derived_claim_ids": receipt.citations.derived_claim_ids,
            "calculation_trace_ids": receipt.citations.calculation_trace_ids,
            "formula_ids": receipt.citations.formula_ids,
            "resolved_obligation_ids": receipt.citations.resolved_obligation_ids,
            "open_obligation_ids": receipt.citations.open_obligation_ids,
            "hazard_ids": receipt.citations.hazard_ids,
            "projection_value_commitments": tuple(
                {
                    "field": item.field,
                    "source_kind": item.source_kind,
                    "source_id": item.source_id,
                    "value_digest": item.value_digest,
                    "digest_alg": item.digest_alg,
                }
                for item in receipt.citations.projection_value_commitments
            ),
            "dependency_fingerprints": tuple(
                {
                    "dependency_kind": item.dependency_kind,
                    "dependency_id": item.dependency_id,
                    "fingerprint": item.fingerprint,
                    "digest_alg": item.digest_alg,
                }
                for item in receipt.citations.dependency_fingerprints
            ),
        }
    return {
        "draft_id": receipt.draft_id,
        "winner_receipt_ids": receipt.winner_receipt_ids,
        "barrier_snapshot": receipt.barrier_snapshot,
        "public_row_id": receipt.public_row_id,
        "projection_id": receipt.projection_id,
        "authorized_fields": receipt.authorized_fields,
        "citations": citations,
    }
```

Implement the inverse:

```python
def commit_receipt_from_body(body: dict[str, Any]) -> CommitReceipt:
    citations_body = body["citations"]
    citations = None
    if citations_body is not None:
        citations = CommitReceiptCitations(
            governance_decision_id=citations_body["governance_decision_id"],
            governance_status=citations_body["governance_status"],
            governance_reasons=tuple(citations_body["governance_reasons"]),
            commit_package_id=citations_body["commit_package_id"],
            commit_package_complete=citations_body["commit_package_complete"],
            subject_id=citations_body["subject_id"],
            projection_id=citations_body["projection_id"],
            authorized_fields=tuple(citations_body["authorized_fields"]),
            profile_id=citations_body["profile_id"],
            report_status=citations_body["report_status"],
            checked_claim_fields=tuple(citations_body["checked_claim_fields"]),
            checked_claim_witness_ids=tuple(citations_body["checked_claim_witness_ids"]),
            semantic_judgment_ids=tuple(citations_body["semantic_judgment_ids"]),
            reference_binding_ids=tuple(citations_body["reference_binding_ids"]),
            derived_claim_fields=tuple(citations_body["derived_claim_fields"]),
            derived_claim_ids=tuple(citations_body["derived_claim_ids"]),
            calculation_trace_ids=tuple(citations_body["calculation_trace_ids"]),
            formula_ids=tuple(citations_body["formula_ids"]),
            resolved_obligation_ids=tuple(citations_body["resolved_obligation_ids"]),
            open_obligation_ids=tuple(citations_body["open_obligation_ids"]),
            hazard_ids=tuple(citations_body["hazard_ids"]),
            projection_value_commitments=tuple(
                ProjectionValueCommitment(
                    field=item["field"],
                    source_kind=item["source_kind"],
                    source_id=item["source_id"],
                    value_digest=item["value_digest"],
                    digest_alg=item["digest_alg"],
                )
                for item in citations_body["projection_value_commitments"]
            ),
            dependency_fingerprints=tuple(
                DependencyFingerprint(
                    dependency_kind=item["dependency_kind"],
                    dependency_id=item["dependency_id"],
                    fingerprint=item["fingerprint"],
                    digest_alg=item["digest_alg"],
                )
                for item in citations_body["dependency_fingerprints"]
            ),
        )
    return CommitReceipt(
        draft_id=body["draft_id"],
        winner_receipt_ids=tuple(body["winner_receipt_ids"]),
        barrier_snapshot=tuple(tuple(item) for item in body["barrier_snapshot"]),
        public_row_id=body["public_row_id"],
        projection_id=body["projection_id"],
        authorized_fields=tuple(body["authorized_fields"]),
        citations=citations,
    )
```

- [ ] **Step 4: Implement `MySQLReceiptLedger`**

Add class:

```python
class MySQLReceiptLedger:
    def __init__(self, connection: Any):
        self.connection = connection

    def record(self, receipt: CommitReceipt) -> CommitReceipt:
        key = ReceiptLedgerKey.from_receipt(receipt)
        existing = self._get_optional(key)
        if existing is None:
            rid = receipt_id(receipt)
            body = commit_receipt_to_body(receipt)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ledger_commit_receipts (
                      receipt_id, public_row_id, projection_id, draft_id,
                      receipt_digest, receipt_body
                    )
                    values (%s, %s, %s, %s, %s, cast(%s as json))
                    """,
                    (
                        rid,
                        receipt.public_row_id,
                        receipt.projection_id,
                        receipt.draft_id,
                        rid.removeprefix("receipt:"),
                        _json_dump(encode_persistence_json(body)),
                    ),
                )
                _insert_receipt_indexes(cursor, rid, receipt)
            self.connection.commit()
            return receipt
        if existing != receipt:
            raise ReceiptConflict(
                f"CommitReceipt ledger root already recorded with different "
                f"content: {key.public_row_id}."
            )
        return existing

    def get(self, *, public_row_id: str, projection_id: str, draft_id: str) -> CommitReceipt:
        key = ReceiptLedgerKey(public_row_id, projection_id, draft_id)
        existing = self._get_optional(key)
        if existing is None:
            raise KeyError(key)
        return existing

    def receipts(self) -> tuple[CommitReceipt, ...]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select receipt_body
                from ledger_commit_receipts
                order by public_row_id, projection_id, draft_id
                """
            )
            return tuple(
                commit_receipt_from_body(decode_persistence_json(_json_load(row[0])))
                for row in cursor.fetchall()
            )

    def _get_optional(self, key: ReceiptLedgerKey) -> CommitReceipt | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select receipt_body
                from ledger_commit_receipts
                where public_row_id = %s and projection_id = %s and draft_id = %s
                """,
                (key.public_row_id, key.projection_id, key.draft_id),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return commit_receipt_from_body(decode_persistence_json(_json_load(row[0])))
```

Implement `_insert_receipt_indexes(cursor, receipt_id, receipt)` by inserting:

```text
receipt.citations.projection_value_commitments
receipt.citations.dependency_fingerprints
receipt_artifact_refs(receipt)
```

Use `role = "receipt_artifact_ref"` for V1. Role refinement can happen later.

- [ ] **Step 5: Run receipt tests**

Use the command from Step 2.

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit receipt ledger**

```bash
git add comp/persistence/mysql.py tests/test_mysql_persistence_spine.py
git commit -m "feat: add mysql receipt ledger"
```

### Task 7: Verify Receipt-Derived Indexes And Replay

**Files:**
- Modify: `tests/test_mysql_persistence_spine.py`

- [ ] **Step 1: Write failing receipt index and replay tests**

Append:

```python
from comp.persistence import receipt_artifact_refs, replay_public_projection
from tests.support.persistence_cases import artifact_store_for_receipt


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
```

- [ ] **Step 2: Run tests to verify they fail if indexes/replay are incomplete**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py::test_mysql_receipt_ledger_populates_receipt_indexes tests/test_mysql_persistence_spine.py::test_mysql_artifact_store_supports_replay_public_projection -q
```

Expected before completing indexes:

```text
FAILED with index count mismatch or replay artifact issue
```

- [ ] **Step 3: Fix index insertion or artifact codec until tests pass**

Do not change assertions unless the observed failure proves the planned count is
wrong. If the count is wrong, inspect `receipt_artifact_refs(receipt)` and align
DB insertion to that function.

- [ ] **Step 4: Run full MySQL spine test file**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py -q
```

Expected:

```text
passed
```

- [ ] **Step 5: Commit replay coverage**

```bash
git add tests/test_mysql_persistence_spine.py comp/persistence/mysql.py
git commit -m "test: cover mysql receipt replay spine"
```

### Task 8: Export MySQL Backend

**Files:**
- Modify: `comp/persistence/__init__.py`
- Test: `tests/test_package_smoke.py`

- [ ] **Step 1: Write failing package export test**

Add to `tests/test_package_smoke.py`:

```python
def test_persistence_exports_mysql_backend_surface():
    from comp.persistence import (
        MySQLArtifactStore,
        MySQLReceiptLedger,
        apply_trust_spine_schema,
    )

    assert MySQLArtifactStore is not None
    assert MySQLReceiptLedger is not None
    assert apply_trust_spine_schema is not None
```

- [ ] **Step 2: Run export test to verify it fails**

```bash
python -m pytest tests/test_package_smoke.py::test_persistence_exports_mysql_backend_surface -q
```

Expected:

```text
FAILED with ImportError
```

- [ ] **Step 3: Export symbols**

Modify `comp/persistence/__init__.py`:

```python
from comp.persistence.mysql import (
    MySQLArtifactStore,
    MySQLReceiptLedger,
    apply_trust_spine_schema,
)
```

Add the same names to `__all__`.

- [ ] **Step 4: Run export test**

```bash
python -m pytest tests/test_package_smoke.py::test_persistence_exports_mysql_backend_surface -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit export**

```bash
git add comp/persistence/__init__.py tests/test_package_smoke.py
git commit -m "feat: export mysql persistence backend"
```

### Task 9: Update Architecture Docs

**Files:**
- Modify: `docs/architecture/production-trust-spine-database.md`
- Modify: `docs/architecture/persistence-ledger-boundary.md`
- Test: `tests/test_package_smoke.py`

- [ ] **Step 1: Write failing doc smoke test**

Add to `tests/test_package_smoke.py`:

```python
def test_production_database_north_star_tracks_v1_mysql_spine():
    db_doc = Path(
        "docs/architecture/production-trust-spine-database.md"
    ).read_text(encoding="utf-8")
    persistence_doc = Path(
        "docs/architecture/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "## 12. Current Implementation Status" in db_doc
    assert "MySQLArtifactStore" in db_doc
    assert "MySQLReceiptLedger" in db_doc
    assert "ledger_receipt_artifact_refs" in db_doc
    assert "MySQL trust spine" in persistence_doc
```

- [ ] **Step 2: Run doc test to verify it fails**

```bash
python -m pytest tests/test_package_smoke.py::test_production_database_north_star_tracks_v1_mysql_spine -q
```

Expected:

```text
FAILED with AssertionError
```

- [ ] **Step 3: Update docs**

Add a `## 12. Current Implementation Status` section to
`production-trust-spine-database.md`:

```text
The first durable spine slice is implemented for MySQL:

comp/persistence/mysql.py
  provides apply_trust_spine_schema, MySQLArtifactStore, and
  MySQLReceiptLedger.

artifact_envelopes
  stores encoded ArtifactEnvelope bodies with digest-preserving persistence
  JSON.

ledger_commit_receipts
  stores append-only CommitReceipt roots keyed by receipt id and ledger key.

ledger_receipt_value_commitments / ledger_receipt_dependency_fingerprints /
ledger_receipt_artifact_refs
  provide receipt-derived query indexes. They are indexes, not independent
  authority.
```

Add a short note to `persistence-ledger-boundary.md` current status:

```text
MySQL trust spine
  adds a first durable backend for artifact envelopes and receipt ledger roots.
```

- [ ] **Step 4: Run doc test**

```bash
python -m pytest tests/test_package_smoke.py::test_production_database_north_star_tracks_v1_mysql_spine -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Commit docs**

```bash
git add docs/architecture/production-trust-spine-database.md docs/architecture/persistence-ledger-boundary.md tests/test_package_smoke.py
git commit -m "docs: record mysql trust spine status"
```

### Task 10: Final Verification And PR

**Files:**
- No new files beyond previous tasks.

- [ ] **Step 1: Run MySQL test file**

```bash
COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py -q
```

Expected:

```text
passed
```

- [ ] **Step 2: Run full suite**

```bash
python -m pytest -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Run domain scenario gate**

```bash
python -m tests.domain_scenarios run-all
```

Expected:

```text
Passed: 17/17
```

- [ ] **Step 4: Check diff**

```bash
git diff --check
git status -sb
```

Expected:

```text
git diff --check has no errors
status shows only intended committed branch state
```

- [ ] **Step 5: Push and open draft PR**

```bash
git push -u origin codex/mysql-trust-spine-v1
@'
## Summary

- Add MySQL-backed ArtifactStore and ReceiptLedger implementations.
- Add V1 trust spine tables and receipt-derived indexes.
- Preserve replay behavior through the existing replay_public_projection API.

## Validation

- python -m pytest -q
- python -m tests.domain_scenarios run-all
- COMP_TEST_MYSQL_HOST=127.0.0.1 COMP_TEST_MYSQL_USER=comp COMP_TEST_MYSQL_PASSWORD=comp COMP_TEST_MYSQL_DATABASE=comp_test python -m pytest tests/test_mysql_persistence_spine.py -q
'@ | Set-Content -Encoding UTF8 .git/pr-body-mysql-trust-spine-v1.md
gh pr create --draft --title "[codex] add mysql trust spine v1" --body-file .git/pr-body-mysql-trust-spine-v1.md
```

## Self-Review

Spec coverage:

```text
Durable artifact store: Tasks 4-5
Durable receipt ledger: Task 6
Receipt-derived indexes: Tasks 6-7
Replay from persisted artifacts: Task 7
Optional DB dependency and CI: Task 2
Docs/status update: Task 9
```

Risk notes:

```text
The persistence JSON codec is a real design risk. It must preserve tuple/list
and Decimal distinctions because existing digest semantics do.

The first PR intentionally avoids workflow, registry, and projection tables.
Adding them before the artifact/receipt spine is proven would create too much
surface area and blur authority boundaries.

Exporting MySQL classes from comp.persistence imports PyMySQL through
comp.persistence.mysql. If this makes base imports require the db extra, change
__init__.py to export a lazy wrapper or document that db extra is needed for the
MySQL backend.

MySQL JSON values should never be treated as canonical digest material. Always
decode through comp.persistence.codec before constructing ArtifactEnvelope or
CommitReceipt objects.
```
