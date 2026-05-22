from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


def test_schema_labels_cover_friendly_authority_surface():
    from comp.schema_labels import SCHEMA_LABELS, schema_label, schema_label_ko

    expected_ko_labels = {
        "ClaimCandidate": "검증 전 입력값",
        "EvidenceRef": "근거자료 위치",
        "CanonicalReference": "확정 기준",
        "CalculatedClaim": "계산값",
        "ValidationReport": "검증 결과",
        "ReviewPackage": "승인 검토 묶음",
        "ReviewDecision": "검토 결정",
        "PublicOutputReceipt": "공개 승인 증표",
        "PublicOutputSpec": "공개 출력 정의",
        "PublicOutput": "공개 결과",
        "ArtifactEnvelope": "감사 산출물 기록",
    }

    assert expected_ko_labels.keys() <= SCHEMA_LABELS.keys()
    for schema_name, ko_label in expected_ko_labels.items():
        assert schema_label(schema_name).ko == ko_label
        assert schema_label_ko(schema_name) == ko_label

    assert "공개 승인 없이는 공개 불가" in schema_label(
        "CalculatedClaim"
    ).authority_ko
    assert schema_label("ArtifactEnvelope").authority_ko == (
        "재검증 가능한 산출물 기록, 공개 승인 권한 없음"
    )


def test_schema_labels_are_display_metadata_not_authority_state():
    from comp.schema_labels import SCHEMA_LABELS, schema_label

    receipt_label = schema_label("PublicOutputReceipt")

    assert not hasattr(receipt_label, "can_authorize_public_output")
    assert not hasattr(receipt_label, "can_project_public_row")
    with pytest.raises(FrozenInstanceError):
        receipt_label.ko = "다른 표시명"
    with pytest.raises(TypeError):
        SCHEMA_LABELS["PublicOutputReceipt"] = receipt_label

    authority_paths = (
        Path("comp/judgment/commit.py"),
        Path("comp/compiler_tool/receipt_builder.py"),
        Path("comp/persistence/ledger.py"),
    )
    for path in authority_paths:
        assert "schema_labels" not in path.read_text(encoding="utf-8")


def test_unknown_schema_label_fails_explicitly():
    from comp.schema_labels import UnknownSchemaLabel, schema_label

    with pytest.raises(UnknownSchemaLabel, match="No schema label registered"):
        schema_label("MissingKernelType")
