"""Render-only Korean validation summary helpers."""

from __future__ import annotations

from typing import Any

from comp.compiler_tool import Hazard, ValidationReport, ValidationRequirement
from comp.schema_labels import schema_label, schema_label_ko
from comp.user_messages import (
    UnknownUserMessage,
    UserMessage,
    user_message_for_reason,
)

_STATUS_KO = {
    "accepted": "검증됨",
    "blocked": "차단됨",
    "review_required": "검토 필요",
    "underconstrained": "정보 부족",
    "unchecked": "미검증",
}

_FALLBACK_REQUIREMENT_MESSAGE = UserMessage(
    key="additional_review_required",
    ko="추가 확인이 필요한 항목입니다.",
    action_ko="담당자가 근거자료와 기준을 확인해 주세요.",
)


def validation_summary_view(report: ValidationReport) -> dict[str, Any]:
    """Build a display-only Korean summary for a validation report."""

    return {
        "label_ko": schema_label_ko("ValidationReport"),
        "status": report.status,
        "status_ko": _STATUS_KO.get(report.status, "상태 확인 필요"),
        "authority_ko": schema_label("ValidationReport").authority_ko,
        "can_make_public_output": report.can_project_public_row,
        "public_output": _public_output_view(report),
        "sections": [
            _count_section("EvidenceRef", len(report.evidence_witnesses)),
            _count_section("CanonicalReference", len(report.reference_bindings)),
            _count_section("CalculatedClaim", len(report.derived_claims)),
        ],
        "open_requirements": [
            _requirement_view(requirement)
            for requirement in report.obligations
        ],
        "resolved_requirements": [
            _requirement_view(requirement)
            for requirement in report.resolved_obligations
        ],
        "review_items": [_review_item_view(hazard) for hazard in report.hazards],
    }


def _public_output_view(report: ValidationReport) -> dict[str, str]:
    return {
        "label_ko": schema_label_ko("PublicOutput"),
        "state_ko": "공개 가능" if report.can_project_public_row else "공개 승인 전",
        "authority_ko": schema_label("PublicOutput").authority_ko,
    }


def _count_section(schema_name: str, count: int) -> dict[str, int | str]:
    return {
        "label_ko": schema_label_ko(schema_name),
        "count": count,
    }


def _requirement_view(requirement: ValidationRequirement) -> dict[str, Any]:
    message = _message_for_requirement(requirement)
    return {
        "label_ko": schema_label_ko("ValidationRequirement"),
        "requirement_id": requirement.obligation_id,
        "field": requirement.field,
        "blocking": requirement.blocking,
        "message_ko": message.ko,
        "action_ko": message.action_ko,
    }


def _message_for_requirement(requirement: ValidationRequirement) -> UserMessage:
    try:
        return user_message_for_reason(requirement.reason)
    except UnknownUserMessage:
        return _FALLBACK_REQUIREMENT_MESSAGE


def _review_item_view(hazard: Hazard) -> dict[str, str]:
    return {
        "label_ko": "검토 필요 항목",
        "field": hazard.field,
        "message_ko": "검토가 필요한 항목입니다.",
        "severity": hazard.severity,
    }


__all__ = ["validation_summary_view"]
