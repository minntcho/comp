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


__all__ = ["TRUST_SPINE_SCHEMA_STATEMENTS", "apply_trust_spine_schema"]
