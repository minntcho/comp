from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class UserMessage:
    key: str
    ko: str
    action_ko: str | None = None


class UnknownUserMessage(KeyError):
    """Raised when no user-facing message is registered for a key or reason."""


_USER_MESSAGES = {
    "missing_evidence": UserMessage(
        key="missing_evidence",
        ko="근거자료가 연결되지 않아 이 값을 검증할 수 없습니다.",
        action_ko="값이 나온 문서, 엑셀, 인증서 등의 위치를 연결해 주세요.",
    ),
    "ambiguous_reference": UserMessage(
        key="ambiguous_reference",
        ko="사용할 기준이 여러 개라 선택이 필요합니다.",
        action_ko="계산에 사용할 확정 기준을 선택해 주세요.",
    ),
    "unsupported_unit": UserMessage(
        key="unsupported_unit",
        ko="지원하지 않는 단위입니다. 단위를 확인해 주세요.",
        action_ko="지원되는 단위로 변환하거나 단위 변환 근거를 추가해 주세요.",
    ),
    "public_output_receipt_required": UserMessage(
        key="public_output_receipt_required",
        ko="공개 결과를 만들려면 공개 승인 증표가 필요합니다.",
        action_ko="검증 결과를 승인 검토한 뒤 공개 승인 증표를 발급해 주세요.",
    ),
    "source_fingerprint_mismatch": UserMessage(
        key="source_fingerprint_mismatch",
        ko="원본자료가 변경되어 감사 재검증에 실패했습니다.",
        action_ko="변경된 원본자료로 다시 검증해 주세요.",
    ),
}

_REASON_MESSAGE_KEYS = {
    "missing_source_witness": "missing_evidence",
    "missing_evidence": "missing_evidence",
    "ambiguous_reference": "ambiguous_reference",
    "multiple_reference_candidates": "ambiguous_reference",
    "unsupported_unit": "unsupported_unit",
    "public_output_receipt_required": "public_output_receipt_required",
    "public_output_requires_receipt": "public_output_receipt_required",
    "source_fingerprint_mismatch": "source_fingerprint_mismatch",
    "dependency_fingerprint_mismatch": "source_fingerprint_mismatch",
}

USER_MESSAGES: Mapping[str, UserMessage] = MappingProxyType(_USER_MESSAGES)
REASON_MESSAGE_KEYS: Mapping[str, str] = MappingProxyType(_REASON_MESSAGE_KEYS)


def user_message(message_key: str) -> UserMessage:
    try:
        return USER_MESSAGES[message_key]
    except KeyError as exc:
        raise UnknownUserMessage(
            f"No user message registered for {message_key!r}."
        ) from exc


def user_message_ko(message_key: str) -> str:
    return user_message(message_key).ko


def user_message_for_reason(reason: str) -> UserMessage:
    try:
        message_key = REASON_MESSAGE_KEYS[reason]
    except KeyError as exc:
        raise UnknownUserMessage(
            f"No user message registered for reason {reason!r}."
        ) from exc
    return user_message(message_key)


__all__ = [
    "REASON_MESSAGE_KEYS",
    "USER_MESSAGES",
    "UnknownUserMessage",
    "UserMessage",
    "user_message",
    "user_message_for_reason",
    "user_message_ko",
]
