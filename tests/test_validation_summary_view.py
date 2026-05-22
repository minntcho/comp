from pathlib import Path

from comp.compiler_tool import Hazard, ValidationReport, ValidationRequirement


def test_validation_summary_view_uses_korean_labels_and_messages():
    from comp.views.validation_summary import validation_summary_view

    report = ValidationReport(
        status="blocked",
        obligations=(
            ValidationRequirement(
                kind="find_source_witness",
                field="co2e_kg",
                reason="missing_source_witness",
                obligation_id="obl-1",
            ),
        ),
        resolved_obligations=(
            ValidationRequirement(
                kind="unit_check",
                field="electricity_mwh",
                reason="unsupported_unit",
                obligation_id="obl-2",
                blocking=False,
            ),
        ),
        hazards=(Hazard(kind="conflict", field="scope2_method", severity="review"),),
    )

    view = validation_summary_view(report)

    assert view["label_ko"] == "검증 결과"
    assert view["status_ko"] == "차단됨"
    assert view["public_output"] == {
        "label_ko": "공개 결과",
        "state_ko": "공개 승인 전",
        "authority_ko": "증표로 검증된 보기, 자체 승인 권한 없음",
    }
    assert view["sections"] == [
        {"label_ko": "근거자료 위치", "count": 0},
        {"label_ko": "확정 기준", "count": 0},
        {"label_ko": "계산값", "count": 0},
    ]
    assert view["open_requirements"] == [
        {
            "label_ko": "보완 필요 항목",
            "requirement_id": "obl-1",
            "field": "co2e_kg",
            "blocking": True,
            "message_ko": "근거자료가 연결되지 않아 이 값을 검증할 수 없습니다.",
            "action_ko": "값이 나온 문서, 엑셀, 인증서 등의 위치를 연결해 주세요.",
        }
    ]
    assert view["resolved_requirements"] == [
        {
            "label_ko": "보완 필요 항목",
            "requirement_id": "obl-2",
            "field": "electricity_mwh",
            "blocking": False,
            "message_ko": "지원하지 않는 단위입니다. 단위를 확인해 주세요.",
            "action_ko": (
                "지원되는 단위로 변환하거나 단위 변환 근거를 추가해 주세요."
            ),
        }
    ]
    assert view["review_items"] == [
        {
            "label_ko": "검토 필요 항목",
            "field": "scope2_method",
            "message_ko": "검토가 필요한 항목입니다.",
            "severity": "review",
        }
    ]


def test_validation_summary_view_falls_back_without_leaking_kernel_terms():
    from comp.views.validation_summary import validation_summary_view

    report = ValidationReport(
        status="review_required",
        obligations=(
            ValidationRequirement(
                kind="reference_search_required",
                field="co2e_kg",
                reason="unknown_reference",
                obligation_id="obl-reference",
            ),
        ),
    )

    view = validation_summary_view(report)

    assert view["open_requirements"][0]["message_ko"] == (
        "추가 확인이 필요한 항목입니다."
    )
    blocked_terms = (
        "ClaimHypothesis",
        "EvidenceWitness",
        "ReferenceCandidate",
        "ReferenceBinding",
        "CommitReceipt",
        "Projection",
        "PublicOutputReceipt",
        "ProofObligation",
    )
    assert not any(term in str(view) for term in blocked_terms)


def test_validation_summary_view_is_presentation_not_authority_state():
    import comp.views.validation_summary as validation_summary
    from comp.views import validation_summary_view

    assert validation_summary_view is validation_summary.validation_summary_view

    source = Path("comp/views/validation_summary.py").read_text(encoding="utf-8")
    assert "comp.schema_labels" in source
    assert "comp.user_messages" in source

    authority_paths = (
        Path("comp/judgment/commit.py"),
        Path("comp/compiler_tool/receipt_builder.py"),
        Path("comp/persistence/ledger.py"),
        Path("comp/persistence/replay.py"),
    )
    for path in authority_paths:
        text = path.read_text(encoding="utf-8")
        assert "validation_summary" not in text
        assert "schema_labels" not in text
        assert "user_messages" not in text
