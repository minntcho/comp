from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest


def test_user_messages_translate_common_kernel_reasons_to_korean_actions():
    from comp.user_messages import (
        USER_MESSAGES,
        user_message_for_reason,
        user_message_ko,
    )

    expected_messages = {
        "missing_evidence": "근거자료가 연결되지 않아 이 값을 검증할 수 없습니다.",
        "ambiguous_reference": "사용할 기준이 여러 개라 선택이 필요합니다.",
        "unsupported_unit": "지원하지 않는 단위입니다. 단위를 확인해 주세요.",
        "public_output_receipt_required": (
            "공개 결과를 만들려면 공개 승인 증표가 필요합니다."
        ),
        "source_fingerprint_mismatch": (
            "원본자료가 변경되어 감사 재검증에 실패했습니다."
        ),
    }

    blocked_terms = (
        "ClaimCandidate",
        "EvidenceRef",
        "ReferenceOption",
        "CanonicalReference",
        "PublicOutputReceipt",
        "Projection",
        "PublicOutputReceipt",
    )
    assert expected_messages.keys() <= USER_MESSAGES.keys()
    for message_key, ko in expected_messages.items():
        assert user_message_ko(message_key) == ko
        assert not any(term in ko for term in blocked_terms)

    assert user_message_for_reason("missing_source_witness").key == "missing_evidence"
    assert user_message_for_reason("unsupported_unit").key == "unsupported_unit"
    assert (
        user_message_for_reason("public_output_receipt_required").key
        == "public_output_receipt_required"
    )


def test_user_messages_are_display_metadata_not_authority_state():
    from comp.user_messages import USER_MESSAGES, user_message

    message = user_message("public_output_receipt_required")

    assert not hasattr(message, "can_authorize_public_output")
    assert not hasattr(message, "can_build_public_output")
    with pytest.raises(FrozenInstanceError):
        message.ko = "다른 메시지"
    with pytest.raises(TypeError):
        USER_MESSAGES["public_output_receipt_required"] = message

    authority_paths = (
        Path("comp/judgment/commit.py"),
        Path("comp/compiler_tool/receipt_builder.py"),
        Path("comp/persistence/ledger.py"),
        Path("comp/persistence/replay.py"),
    )
    for path in authority_paths:
        assert "user_messages" not in path.read_text(encoding="utf-8")


def test_unknown_user_message_fails_explicitly():
    from comp.user_messages import UnknownUserMessage, user_message

    with pytest.raises(UnknownUserMessage, match="No user message registered"):
        user_message("missing_product_surface")
