from __future__ import annotations

import json
import hashlib
from typing import Any

from comp.judgment.receipts import PublicOutputReceipt
from comp.persistence.codec import (
    commit_receipt_from_body,
    commit_receipt_to_body,
    decode_persistence_json,
    encode_persistence_json,
)
from comp.persistence.envelope import ArtifactEnvelope
from comp.persistence.ledger import (
    ArtifactConflict,
    ReceiptConflict,
    ReceiptLedgerKey,
    verify_artifact_envelope,
)
from comp.persistence.replay import receipt_artifact_refs


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
                    values (%s, %s, %s, %s, %s, %s, %s)
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


class MySQLReceiptLedger:
    def __init__(self, connection: Any):
        self.connection = connection

    def record(self, receipt: PublicOutputReceipt) -> PublicOutputReceipt:
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
                    values (%s, %s, %s, %s, %s, %s)
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
                f"Public-output receipt ledger root already recorded with "
                f"different content: {key.public_row_id}."
            )
        return existing

    def get(
        self,
        *,
        public_row_id: str,
        projection_id: str,
        draft_id: str,
    ) -> PublicOutputReceipt:
        key = ReceiptLedgerKey(public_row_id, projection_id, draft_id)
        existing = self._get_optional(key)
        if existing is None:
            raise KeyError(key)
        return existing

    def receipts(self) -> tuple[PublicOutputReceipt, ...]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select receipt_body
                from ledger_commit_receipts
                order by public_row_id, projection_id, draft_id
                """
            )
            return tuple(_commit_receipt_from_row(row) for row in cursor.fetchall())

    def _get_optional(self, key: ReceiptLedgerKey) -> PublicOutputReceipt | None:
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
        return _commit_receipt_from_row(row)


def receipt_id(receipt: PublicOutputReceipt) -> str:
    body = commit_receipt_to_body(receipt)
    canonical = _json_dump(encode_persistence_json(body))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"receipt:sha256:{digest}"


def _insert_receipt_indexes(
    cursor: Any,
    rid: str,
    receipt: PublicOutputReceipt,
) -> None:
    if receipt.citations is None:
        return
    for commitment in receipt.citations.projection_value_commitments:
        cursor.execute(
            """
            insert into ledger_receipt_value_commitments (
              receipt_id, field, source_kind, source_id, value_digest, digest_alg
            )
            values (%s, %s, %s, %s, %s, %s)
            """,
            (
                rid,
                commitment.field,
                commitment.source_kind,
                commitment.source_id,
                commitment.value_digest,
                commitment.digest_alg,
            ),
        )
    for fingerprint in receipt.citations.dependency_fingerprints:
        cursor.execute(
            """
            insert into ledger_receipt_dependency_fingerprints (
              receipt_id, dependency_kind, dependency_id, fingerprint, digest_alg
            )
            values (%s, %s, %s, %s, %s)
            """,
            (
                rid,
                fingerprint.dependency_kind,
                fingerprint.dependency_id,
                fingerprint.fingerprint,
                fingerprint.digest_alg,
            ),
        )
    for ref in receipt_artifact_refs(receipt):
        cursor.execute(
            """
            insert into ledger_receipt_artifact_refs (
              receipt_id, artifact_id, artifact_kind, role
            )
            values (%s, %s, %s, %s)
            """,
            (rid, ref.artifact_id, ref.artifact_kind, "receipt_artifact_ref"),
        )


def _artifact_envelope_from_row(row: Any) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_id=row[0],
        artifact_kind=row[1],
        schema_version=row[2],
        body_digest=row[3],
        body=decode_persistence_json(_json_load(row[4])),
        source_refs=decode_persistence_json(_json_load(row[5])),
        meta=decode_persistence_json(_json_load(row[6])),
    )


def _commit_receipt_from_row(row: Any) -> PublicOutputReceipt:
    return commit_receipt_from_body(decode_persistence_json(_json_load(row[0])))


def _json_dump(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _json_load(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


__all__ = [
    "MySQLReceiptLedger",
    "MySQLArtifactStore",
    "TRUST_SPINE_SCHEMA_STATEMENTS",
    "apply_trust_spine_schema",
    "commit_receipt_from_body",
    "commit_receipt_to_body",
    "receipt_id",
]
