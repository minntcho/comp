from decimal import Decimal

import pytest

from comp.persistence import ArtifactEnvelope, artifact_digest


def test_artifact_envelope_body_digest_is_stable_for_canonical_body():
    first = ArtifactEnvelope.from_body(
        artifact_id="artifact:claim:1",
        artifact_kind="checked_claim",
        schema_version="v1",
        body={
            "field": "electricity_kwh",
            "value": 1200,
            "meta": {"unit": "kWh", "source": "span-1"},
        },
    )
    second = ArtifactEnvelope.from_body(
        artifact_id="artifact:claim:1",
        artifact_kind="checked_claim",
        schema_version="v1",
        body={
            "meta": {"source": "span-1", "unit": "kWh"},
            "value": 1200,
            "field": "electricity_kwh",
        },
    )

    assert first.body_digest == second.body_digest
    assert first.body_digest.startswith("sha256:")


def test_artifact_digest_changes_when_body_kind_or_schema_changes():
    base = artifact_digest(
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": 1200},
    )

    assert artifact_digest(
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": 1201},
    ) != base
    assert artifact_digest(
        artifact_kind="derived_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": 1200},
    ) != base
    assert artifact_digest(
        artifact_kind="checked_claim",
        schema_version="v2",
        body={"field": "electricity_kwh", "value": 1200},
    ) != base


def test_artifact_envelope_metadata_is_outside_body_digest():
    first = ArtifactEnvelope.from_body(
        artifact_id="artifact:claim:1",
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": 1200},
        source_refs=("span-1",),
        meta=(("stored_at", "2026-05-20T00:00:00Z"),),
    )
    second = ArtifactEnvelope.from_body(
        artifact_id="artifact:claim:1",
        artifact_kind="checked_claim",
        schema_version="v1",
        body={"field": "electricity_kwh", "value": 1200},
        source_refs=("span-2",),
        meta=(("stored_at", "2026-05-21T00:00:00Z"),),
    )

    assert first.body_digest == second.body_digest
    assert first.source_refs != second.source_refs
    assert first.meta != second.meta


def test_artifact_digest_preserves_scalar_types():
    digests = {
        artifact_digest(
            artifact_kind="projection_value",
            schema_version="v1",
            body={"value": value},
        )
        for value in (1200, 1200.0, "1200", Decimal("1200.0"), True)
    }

    assert len(digests) == 5


def test_artifact_digest_rejects_non_finite_numbers_and_non_string_keys():
    with pytest.raises(ValueError, match="finite float"):
        artifact_digest(
            artifact_kind="projection_value",
            schema_version="v1",
            body={"value": float("nan")},
        )

    with pytest.raises(ValueError, match="finite decimal"):
        artifact_digest(
            artifact_kind="projection_value",
            schema_version="v1",
            body={"value": Decimal("NaN")},
        )

    with pytest.raises(TypeError, match="string keys"):
        artifact_digest(
            artifact_kind="projection_value",
            schema_version="v1",
            body={1: "numeric key"},
        )


def test_artifact_envelope_requires_stable_identity_fields():
    with pytest.raises(ValueError, match="artifact_id"):
        ArtifactEnvelope.from_body(
            artifact_id="",
            artifact_kind="checked_claim",
            schema_version="v1",
            body={"field": "electricity_kwh"},
        )

    with pytest.raises(ValueError, match="artifact_kind"):
        ArtifactEnvelope.from_body(
            artifact_id="artifact:claim:1",
            artifact_kind="",
            schema_version="v1",
            body={"field": "electricity_kwh"},
        )

    with pytest.raises(ValueError, match="schema_version"):
        ArtifactEnvelope.from_body(
            artifact_id="artifact:claim:1",
            artifact_kind="checked_claim",
            schema_version="",
            body={"field": "electricity_kwh"},
        )
