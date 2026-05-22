from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class SchemaLabel:
    ko: str
    description_ko: str
    authority_ko: str


class UnknownSchemaLabel(KeyError):
    """Raised when a display label is requested for an unknown schema name."""


_SCHEMA_LABELS = {
    "ClaimCandidate": SchemaLabel(
        ko="검증 전 입력값",
        description_ko=(
            "공급사, 파서, 또는 사용자가 제출했지만 아직 검증되지 않은 값입니다."
        ),
        authority_ko="공개 불가",
    ),
    "EvidenceRef": SchemaLabel(
        ko="근거자료 위치",
        description_ko="값이 확인된 문서, 엑셀, 인증서 등의 위치입니다.",
        authority_ko="값 검증 근거로만 사용 가능",
    ),
    "ValidationRequirement": SchemaLabel(
        ko="보완 필요 항목",
        description_ko="검증 결과가 깨끗해지기 전에 해결해야 하는 확인사항입니다.",
        authority_ko="해결 전 공개 불가",
    ),
    "ReferenceOption": SchemaLabel(
        ko="기준 후보",
        description_ko="계산 기준으로 검토할 수 있는 후보 자료입니다.",
        authority_ko="후보만으로는 계산 불가",
    ),
    "CanonicalReference": SchemaLabel(
        ko="확정 기준",
        description_ko="계산에 사용할 수 있도록 결정적으로 선택된 기준입니다.",
        authority_ko="계산 가능, 공개 승인 불가",
    ),
    "CalculationTrace": SchemaLabel(
        ko="계산 내역",
        description_ko="계산식, 입력값, 산출값을 재검토할 수 있게 남긴 기록입니다.",
        authority_ko="재현성 기록, 공개 승인 불가",
    ),
    "CalculatedClaim": SchemaLabel(
        ko="계산값",
        description_ko="확정 기준과 입력값을 사용해 계산된 결과입니다.",
        authority_ko="계산 완료, 공개 승인 없이는 공개 불가",
    ),
    "ValidationReport": SchemaLabel(
        ko="검증 결과",
        description_ko="입력값, 근거자료, 기준, 계산값의 검증 상태를 요약한 결과입니다.",
        authority_ko="상태 요약, 공개 승인 불가",
    ),
    "ReviewPackage": SchemaLabel(
        ko="승인 검토 묶음",
        description_ko="공개 승인 여부를 검토하기 위해 검증 결과를 고정한 묶음입니다.",
        authority_ko="승인 전 검토 자료, 공개 승인 불가",
    ),
    "ReviewDecision": SchemaLabel(
        ko="검토 결정",
        description_ko="승인 검토 묶음에 대한 commit, hold, reject 결정입니다.",
        authority_ko="commit 결정만 공개 승인 증표 발급 가능",
    ),
    "PublicOutputReceipt": SchemaLabel(
        ko="공개 승인 증표",
        description_ko=(
            "특정 공개 결과를 내보낼 수 있음을 증명하는 승인 기록입니다."
        ),
        authority_ko="지정된 공개 결과만 승인 가능",
    ),
    "PublicOutputReceiptCitations": SchemaLabel(
        ko="공개 승인 근거",
        description_ko="공개 승인 증표가 근거로 삼은 검토 묶음과 의존성 기록입니다.",
        authority_ko="승인 증표 검증 근거, 독립 공개 승인 불가",
    ),
    "PublicOutputSpec": SchemaLabel(
        ko="공개 출력 정의",
        description_ko="외부에 보여줄 필드와 공개 결과의 모양을 정의합니다.",
        authority_ko="출력 형태 정의, 공개 승인 불가",
    ),
    "PublicOutputBlocked": SchemaLabel(
        ko="공개 출력 차단",
        description_ko="공개 결과를 만들 수 없는 이유를 나타내는 오류입니다.",
        authority_ko="차단 상태 설명, 공개 승인 불가",
    ),
    "PublicOutput": SchemaLabel(
        ko="공개 결과",
        description_ko="공개 승인 증표로 검증된 뒤 외부에 보여줄 최종 값입니다.",
        authority_ko="증표로 검증된 보기, 자체 승인 권한 없음",
    ),
    "ArtifactEnvelope": SchemaLabel(
        ko="감사 산출물 기록",
        description_ko=(
            "스키마 버전과 digest로 무결성을 검증할 수 있는 재검증 산출물 봉투입니다."
        ),
        authority_ko="재검증 가능한 산출물 기록, 공개 승인 권한 없음",
    ),
}

SCHEMA_LABELS: Mapping[str, SchemaLabel] = MappingProxyType(_SCHEMA_LABELS)


def schema_label(schema_name: str) -> SchemaLabel:
    try:
        return SCHEMA_LABELS[schema_name]
    except KeyError as exc:
        raise UnknownSchemaLabel(
            f"No schema label registered for {schema_name!r}."
        ) from exc


def schema_label_ko(schema_name: str) -> str:
    return schema_label(schema_name).ko


__all__ = [
    "SCHEMA_LABELS",
    "SchemaLabel",
    "UnknownSchemaLabel",
    "schema_label",
    "schema_label_ko",
]
