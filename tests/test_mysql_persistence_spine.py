import os
from decimal import Decimal

import pytest

from comp.persistence import ArtifactEnvelope, verify_artifact_envelope


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
